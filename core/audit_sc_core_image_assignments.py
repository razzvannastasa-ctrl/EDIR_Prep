"""
Audit and conservatively fix SC/CORE image assignments.

Outputs go under C:\\Users\\Razvan\\Documents\\Radiologie\\backups.

Default use:
    py -m core.audit_sc_core_image_assignments

Apply high-confidence fixes:
    py -m core.audit_sc_core_image_assignments --apply
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import re
import shutil
import sqlite3
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "edir_prep.db"
CROPS_DIR = BASE_DIR / "data" / "crops"
BACKUPS_DIR = Path(r"C:\Users\Razvan\Documents\Radiologie\backups")

IMAGE_DEPENDENT_RE = re.compile(
    r"\b("
    r"image|images|fig|figure|radiograph|x-?ray|chest x|plain film|ct|cta|ctpa|"
    r"mri|mr\b|ultrasound|sonograph|doppler|angiogram|angiography|fluoroscopy|"
    r"scan|window|sequence|phase|mpr|reconstruction"
    r")\b",
    re.I,
)
MODALITY_RE = re.compile(
    r"\b(radiograph|x-?ray|plain film|ctpa|cta|ct|mri|mr\b|ultrasound|sonograph|doppler|angiogram|angiography|fluoroscopy)\b",
    re.I,
)


@dataclass
class ImageRef:
    path: str
    file: str
    exists: bool
    page: int | None
    index: int | None
    width: int | None
    height: int | None
    dhash: int | None


@dataclass
class Finding:
    severity: str
    kind: str
    case_id: int
    source: str
    section: str
    chapter: str
    case_number: int
    qid: int | None
    q_number: int | None
    message: str
    paths: list[str]


@dataclass
class Fix:
    kind: str
    case_id: int
    source: str
    section: str
    chapter: str
    case_number: int
    qid: int
    q_number: int
    field: str
    old_images: list[str]
    new_images: list[str]
    reason: str
    pdf_checked: bool = False


def _safe_json_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except Exception:
        return []
    return parsed if isinstance(parsed, list) else []


def _image_file(path: str) -> Path:
    if path.startswith("data/"):
        return BASE_DIR / path
    return Path(path)


def _parse_page_index(path: str) -> tuple[int | None, int | None]:
    name = Path(path).name
    patterns = [
        r"_p(\d+)_i(\d+)",
        r"p(\d+)_img(\d+)",
        r"page_(\d+)",
        r"answer_p(\d+)",
    ]
    for pat in patterns:
        m = re.search(pat, name)
        if m:
            page = int(m.group(1))
            idx = int(m.group(2)) if m.lastindex and m.lastindex >= 2 else None
            return page, idx
    return None, None


def _dhash(path: Path) -> tuple[int | None, int | None, int | None]:
    try:
        with Image.open(path) as img:
            width, height = img.size
            gray = img.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
            pix = list(gray.getdata())
            bits = 0
            for row in range(8):
                for col in range(8):
                    bits = (bits << 1) | int(pix[row * 9 + col] > pix[row * 9 + col + 1])
            return bits, width, height
    except Exception:
        return None, None, None


def _hamming(a: int | None, b: int | None) -> int | None:
    if a is None or b is None:
        return None
    return (a ^ b).bit_count()


def _image_ref(path: str, cache: dict[str, ImageRef]) -> ImageRef:
    if path in cache:
        return cache[path]
    file_path = _image_file(path)
    page, idx = _parse_page_index(path)
    dh, width, height = _dhash(file_path) if file_path.exists() else (None, None, None)
    ref = ImageRef(
        path=path,
        file=file_path.name,
        exists=file_path.exists(),
        page=page,
        index=idx,
        width=width,
        height=height,
        dhash=dh,
    )
    cache[path] = ref
    return ref


def _rowdict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def load_cases() -> list[dict[str, Any]]:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    case_rows = con.execute(
        """
        SELECT c.id, c.case_number, c.source, c.section, c.chapter_id,
               ch.title AS chapter, c.clinical_vignette, c.original_answer_pages
        FROM cases c
        JOIN chapters ch ON ch.id = c.chapter_id
        WHERE c.section IN ('sc', 'core')
        ORDER BY c.source, c.section, ch.number, c.case_number, c.id
        """
    ).fetchall()
    cases: list[dict[str, Any]] = []
    for case_row in case_rows:
        case = _rowdict(case_row)
        q_rows = con.execute(
            """
            SELECT q.id AS qid, q.q_number, q.question_text, q.q_type, q.page_images,
                   q.video_links, a.page_images AS answer_images
            FROM questions q
            LEFT JOIN answers a ON a.question_id = q.id
            WHERE q.case_id = ?
            ORDER BY q.q_number, q.id
            """,
            (case["id"],),
        ).fetchall()
        case["questions"] = [_rowdict(q) for q in q_rows]
        cases.append(case)
    con.close()
    return cases


def _add_finding(findings: list[Finding], case: dict[str, Any], q: dict[str, Any] | None, severity: str, kind: str, message: str, paths: list[str] | None = None) -> None:
    findings.append(
        Finding(
            severity=severity,
            kind=kind,
            case_id=case["id"],
            source=case["source"],
            section=case["section"],
            chapter=case["chapter"],
            case_number=case["case_number"],
            qid=q["qid"] if q else None,
            q_number=q["q_number"] if q else None,
            message=message,
            paths=paths or [],
        )
    )


def audit_cases(cases: list[dict[str, Any]], cache: dict[str, ImageRef]) -> tuple[list[Finding], list[Fix]]:
    findings: list[Finding] = []
    fixes: list[Fix] = []

    by_case_id = {c["id"]: c for c in cases}
    grouped: dict[tuple[str, str, int], list[dict[str, Any]]] = {}
    for case in cases:
        grouped.setdefault((case["source"], case["section"], case["chapter_id"]), []).append(case)

    for case in cases:
        original_answer_pages = _safe_json_list(case.get("original_answer_pages"))
        answer_page_nums = {_parse_page_index(p)[0] for p in original_answer_pages}
        answer_page_nums.discard(None)
        all_q_images: list[tuple[dict[str, Any], str, ImageRef]] = []

        for q in case["questions"]:
            for field, field_name in (("page_images", "question"), ("answer_images", "answer")):
                imgs = _safe_json_list(q.get(field))
                if len(imgs) != len(set(imgs)):
                    deduped = list(dict.fromkeys(imgs))
                    _add_finding(
                        findings,
                        case,
                        q,
                        "fixable",
                        "duplicate_path_same_field",
                        f"Duplicate image path(s) in {field_name} image list.",
                        imgs,
                    )
                    fixes.append(
                        Fix(
                            kind="dedupe_paths",
                            case_id=case["id"],
                            source=case["source"],
                            section=case["section"],
                            chapter=case["chapter"],
                            case_number=case["case_number"],
                            qid=q["qid"],
                            q_number=q["q_number"],
                            field=field,
                            old_images=imgs,
                            new_images=deduped,
                            reason=f"Remove duplicate paths from {field_name} image list.",
                        )
                    )

                for path in imgs:
                    ref = _image_ref(path, cache)
                    if not ref.exists:
                        _add_finding(findings, case, q, "manual", "missing_file", "Referenced image file does not exist.", [path])
                    if field == "page_images":
                        all_q_images.append((q, path, ref))
                        if ref.page in answer_page_nums:
                            _add_finding(
                                findings,
                                case,
                                q,
                                "manual",
                                "answer_page_image_on_question",
                                "Question-side image appears to come from this case's original answer page.",
                                [path],
                            )

            q_imgs = _safe_json_list(q.get("page_images"))
            a_imgs = _safe_json_list(q.get("answer_images"))
            q_text = q.get("question_text") or ""
            if IMAGE_DEPENDENT_RE.search(q_text) and not q_imgs:
                other_case_imgs = any(_safe_json_list(x.get("page_images")) for x in case["questions"])
                if other_case_imgs:
                    _add_finding(
                        findings,
                        case,
                        q,
                        "manual",
                        "image_dependent_question_empty",
                        "Question appears image-dependent but has no question-side images.",
                        [],
                    )
            if q_imgs and a_imgs:
                overlap = sorted(set(q_imgs) & set(a_imgs))
                if overlap:
                    _add_finding(
                        findings,
                        case,
                        q,
                        "manual",
                        "question_answer_image_overlap",
                        "Same image appears on question and answer sides.",
                        overlap,
                    )

        image_dependent = [
            q for q in case["questions"]
            if IMAGE_DEPENDENT_RE.search(q.get("question_text") or "") and _safe_json_list(q.get("page_images"))
        ]
        seen_sets: dict[tuple[str, ...], dict[str, Any]] = {}
        for q in image_dependent:
            imgs = tuple(_safe_json_list(q.get("page_images")))
            if not imgs:
                continue
            prev = seen_sets.get(imgs)
            if prev and imgs:
                _add_finding(
                    findings,
                    case,
                    q,
                    "manual",
                    "identical_image_set_on_multiple_image_questions",
                    f"Same full question image set as Q{prev['q_number']}; verify this is intentional.",
                    list(imgs),
                )
            else:
                seen_sets[imgs] = q

        modality_questions = [
            q for q in case["questions"]
            if MODALITY_RE.search(q.get("question_text") or "") and _safe_json_list(q.get("page_images"))
        ]
        if len(modality_questions) >= 2:
            _add_finding(
                findings,
                case,
                None,
                "manual",
                "staged_modality_case_review",
                "Multiple modality/stage-specific image questions; review contact sheet for ordering/grouping.",
                [],
            )

    # Adjacent visual-duplicate contamination proposals.
    for key, source_cases in grouped.items():
        source_cases = sorted(source_cases, key=lambda c: (c["case_number"], c["id"]))
        for current, nxt in zip(source_cases, source_cases[1:]):
            current_q_imgs: list[tuple[dict[str, Any], str, ImageRef]] = []
            next_q_imgs: list[tuple[dict[str, Any], str, ImageRef]] = []
            for q in current["questions"]:
                for p in _safe_json_list(q.get("page_images")):
                    current_q_imgs.append((q, p, _image_ref(p, cache)))
            for q in nxt["questions"][:2]:
                for p in _safe_json_list(q.get("page_images")):
                    next_q_imgs.append((q, p, _image_ref(p, cache)))
            for cq, cp, cref in current_q_imgs:
                for nq, np, nref in next_q_imgs:
                    dist = _hamming(cref.dhash, nref.dhash)
                    if dist is None or dist > 3:
                        continue
                    if cp == np:
                        continue
                    c_page = cref.page if cref.page is not None else -1
                    n_page = nref.page if nref.page is not None else -1
                    # Conservative: only treat adjacent-page or same-page duplicate as contamination.
                    if c_page >= 0 and n_page >= 0 and abs(c_page - n_page) <= 1:
                        old_imgs = _safe_json_list(cq.get("page_images"))
                        if cp in old_imgs and len(old_imgs) > 1:
                            new_imgs = [x for x in old_imgs if x != cp]
                            _add_finding(
                                findings,
                                current,
                                cq,
                                "fixable",
                                "adjacent_case_duplicate_contamination",
                                f"Image is visually duplicated in next case Q{nq['q_number']} and is likely page-boundary contamination.",
                                [cp, np],
                            )
                            fixes.append(
                                Fix(
                                    kind="remove_adjacent_duplicate_contamination",
                                    case_id=current["id"],
                                    source=current["source"],
                                    section=current["section"],
                                    chapter=current["chapter"],
                                    case_number=current["case_number"],
                                    qid=cq["qid"],
                                    q_number=cq["q_number"],
                                    field="page_images",
                                    old_images=old_imgs,
                                    new_images=new_imgs,
                                    reason=f"Remove image visually duplicated in next case {nxt['id']} Q{nq['q_number']}: {np}",
                                )
                            )

    # Deduplicate fixes on qid/field/new_images.
    unique: dict[tuple[int, str, tuple[str, ...]], Fix] = {}
    for fix in fixes:
        unique[(fix.qid, fix.field, tuple(fix.new_images))] = fix
    return findings, list(unique.values())


def _draw_wrapped(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str, width: int, font: ImageFont.ImageFont, fill: str = "black") -> int:
    x, y = xy
    line = ""
    for word in text.split():
        candidate = (line + " " + word).strip()
        if draw.textlength(candidate, font=font) <= width:
            line = candidate
        else:
            draw.text((x, y), line, font=font, fill=fill)
            y += 14
            line = word
    if line:
        draw.text((x, y), line, font=font, fill=fill)
        y += 14
    return y


def write_contact_sheets(out_dir: Path, cases: list[dict[str, Any]], findings: list[Finding], max_cases: int) -> int:
    flagged_ids = []
    for f in findings:
        if f.case_id not in flagged_ids:
            flagged_ids.append(f.case_id)
    case_by_id = {c["id"]: c for c in cases}
    contact_dir = out_dir / "contact_sheets"
    contact_dir.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default()
    written = 0
    for case_id in flagged_ids[:max_cases]:
        case = case_by_id[case_id]
        rows: list[tuple[str, list[str]]] = []
        for q in case["questions"]:
            label = f"Q{q['q_number']} id={q['qid']}: {(q.get('question_text') or '').replace(chr(10), ' ')[:180]}"
            imgs = _safe_json_list(q.get("page_images")) + _safe_json_list(q.get("answer_images"))
            rows.append((label, imgs))
        width = 1200
        row_h = 210
        height = 100 + row_h * max(1, len(rows))
        sheet = Image.new("RGB", (width, height), "white")
        draw = ImageDraw.Draw(sheet)
        title = f"case {case_id} | {case['source']} | {case['section']} | {case['chapter']} | #{case['case_number']}"
        y = _draw_wrapped(draw, (10, 10), title, width - 20, font, "black") + 8
        case_findings = [f for f in findings if f.case_id == case_id]
        y = _draw_wrapped(draw, (10, y), "; ".join(f"{f.kind}: {f.message}" for f in case_findings[:4]), width - 20, font, "red") + 8
        for label, imgs in rows:
            draw.text((10, y), label, font=font, fill="black")
            x = 10
            thumb_y = y + 18
            for img_path in imgs[:8]:
                file_path = _image_file(img_path)
                if not file_path.exists():
                    draw.rectangle((x, thumb_y, x + 130, thumb_y + 130), outline="red")
                    draw.text((x, thumb_y + 55), "missing", font=font, fill="red")
                    x += 145
                    continue
                try:
                    with Image.open(file_path) as im:
                        im = im.convert("RGB")
                        im.thumbnail((130, 130))
                        sheet.paste(im, (x, thumb_y))
                        draw.text((x, thumb_y + 134), Path(img_path).name[:22], font=font, fill="black")
                except Exception:
                    draw.rectangle((x, thumb_y, x + 130, thumb_y + 130), outline="red")
                    draw.text((x, thumb_y + 55), "error", font=font, fill="red")
                x += 145
            y += row_h
        out = contact_dir / f"case_{case_id}_{case['source'].lower().replace(' ', '_')}_{case['section']}.jpg"
        sheet.save(out, quality=88)
        written += 1
    return written


def write_reports(out_dir: Path, cases: list[dict[str, Any]], findings: list[Finding], fixes: list[Fix], cache: dict[str, ImageRef], contact_sheet_limit: int) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    audit_json = out_dir / "audit_findings.json"
    fixes_json = out_dir / "proposed_fixes.json"
    image_cache_json = out_dir / "image_cache.json"
    audit_csv = out_dir / "audit_findings.csv"

    audit_json.write_text(json.dumps([asdict(f) for f in findings], indent=2), encoding="utf-8")
    fixes_json.write_text(json.dumps([asdict(f) for f in fixes], indent=2), encoding="utf-8")
    image_cache_json.write_text(json.dumps({k: asdict(v) for k, v in cache.items()}, indent=2), encoding="utf-8")

    with audit_csv.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(asdict(findings[0]).keys()) if findings else ["severity", "kind"])
        writer.writeheader()
        for f in findings:
            writer.writerow(asdict(f))

    sheets = write_contact_sheets(out_dir, cases, findings, contact_sheet_limit)
    return {
        "audit_json": str(audit_json),
        "audit_csv": str(audit_csv),
        "proposed_fixes_json": str(fixes_json),
        "image_cache_json": str(image_cache_json),
        "contact_sheets_written": sheets,
    }


def backup_db(out_dir: Path) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = BACKUPS_DIR / f"edir_prep_before_sc_core_image_audit_apply_{stamp}.db"
    shutil.copy2(DB_PATH, backup)
    (out_dir / "db_backup_path.txt").write_text(str(backup), encoding="utf-8")
    return backup


def apply_fixes(fixes: list[Fix], out_dir: Path) -> list[dict[str, Any]]:
    backup = backup_db(out_dir)
    log: list[dict[str, Any]] = []
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("BEGIN")
        for fix in fixes:
            if fix.field == "page_images":
                con.execute("UPDATE questions SET page_images=? WHERE id=?", (json.dumps(fix.new_images), fix.qid))
            elif fix.field == "answer_images":
                con.execute("UPDATE answers SET page_images=? WHERE question_id=?", (json.dumps(fix.new_images), fix.qid))
            else:
                raise ValueError(f"Unsupported fix field: {fix.field}")
            entry = asdict(fix)
            entry["db_backup"] = str(backup)
            log.append(entry)
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
    (out_dir / "remediation_log.json").write_text(json.dumps(log, indent=2), encoding="utf-8")
    return log


def regression_checks() -> list[str]:
    issues: list[str] = []
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    # Known fixed example: Essential Guide Chest SC2 Q4 should not contain SC3 X-ray.
    row = con.execute("SELECT page_images FROM questions WHERE id=69").fetchone()
    if row and "p104_img00.png" in (row["page_images"] or ""):
        issues.append("Regression failed: Essential Guide Chest SC2 Q4 still contains p104_img00.png")
    # Known fixed example: FRCR VA-shunt Q1/Q2 split.
    q1 = con.execute("SELECT page_images FROM questions WHERE id=701").fetchone()
    q2 = con.execute("SELECT page_images FROM questions WHERE id=702").fetchone()
    if q1 and "p154_i01" not in (q1["page_images"] or ""):
        issues.append("Regression failed: VA-shunt Q1 does not contain portable radiograph p154_i01")
    if q1 and "p151_i00" in (q1["page_images"] or ""):
        issues.append("Regression failed: VA-shunt Q1 still contains CT/angiogram p151_i00")
    if q2 and "p151_i00" not in (q2["page_images"] or ""):
        issues.append("Regression failed: VA-shunt Q2 does not contain CT/angiogram p151_i00")
    if q2 and "p154_i01" in (q2["page_images"] or ""):
        issues.append("Regression failed: VA-shunt Q2 still contains radiograph p154_i01")
    con.close()
    return issues


def summarize(cases: list[dict[str, Any]], findings: list[Finding], fixes: list[Fix], reports: dict[str, Any], applied: list[dict[str, Any]] | None, out_dir: Path) -> dict[str, Any]:
    by_kind: dict[str, int] = {}
    by_severity: dict[str, int] = {}
    for f in findings:
        by_kind[f.kind] = by_kind.get(f.kind, 0) + 1
        by_severity[f.severity] = by_severity.get(f.severity, 0) + 1
    summary = {
        "timestamp": out_dir.name.replace("sc_core_image_audit_", ""),
        "cases_audited": len(cases),
        "questions_audited": sum(len(c["questions"]) for c in cases),
        "cases_flagged": len({f.case_id for f in findings}),
        "findings": len(findings),
        "findings_by_kind": by_kind,
        "findings_by_severity": by_severity,
        "proposed_high_confidence_fixes": len(fixes),
        "applied_fixes": len(applied or []),
        "regression_issues": regression_checks(),
        "reports": reports,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Apply high-confidence fixes after report generation.")
    parser.add_argument("--contact-sheet-limit", type=int, default=250, help="Maximum flagged cases to render as contact sheets.")
    args = parser.parse_args()

    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = BACKUPS_DIR / f"sc_core_image_audit_{stamp}"
    cache: dict[str, ImageRef] = {}
    cases = load_cases()
    findings, fixes = audit_cases(cases, cache)
    reports = write_reports(out_dir, cases, findings, fixes, cache, args.contact_sheet_limit)
    applied = apply_fixes(fixes, out_dir) if args.apply and fixes else None
    summary = summarize(cases, findings, fixes, reports, applied, out_dir)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()

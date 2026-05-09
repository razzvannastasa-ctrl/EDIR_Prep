"""Push files to GitHub via the REST API (used by the admin panel to persist DB and image changes)."""
import base64
import requests
from pathlib import Path

_API = "https://api.github.com"
_HEADERS = {"Accept": "application/vnd.github.v3+json"}
_DB_REPO_PATH = "data/edir_prep.db"


def _headers(token: str) -> dict:
    return {**_HEADERS, "Authorization": f"token {token}"}


def _get_sha(token: str, repo: str, path: str, branch: str) -> str | None:
    r = requests.get(
        f"{_API}/repos/{repo}/contents/{path}",
        headers=_headers(token),
        params={"ref": branch},
        timeout=15,
    )
    if r.status_code == 200:
        return r.json().get("sha")
    return None


def push_bytes(token: str, repo: str, path: str, data: bytes, msg: str, branch: str = "main") -> None:
    sha = _get_sha(token, repo, path, branch)
    payload: dict = {
        "message": msg,
        "content": base64.b64encode(data).decode(),
        "branch": branch,
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(
        f"{_API}/repos/{repo}/contents/{path}",
        headers=_headers(token),
        json=payload,
        timeout=60,
    )
    r.raise_for_status()


def push_db(token: str, repo: str, db_path: Path, branch: str = "main") -> None:
    push_bytes(token, repo, _DB_REPO_PATH, db_path.read_bytes(), "Admin: update DB", branch)


def push_image(token: str, repo: str, local_path: Path, repo_path: str, branch: str = "main") -> None:
    push_bytes(token, repo, repo_path, local_path.read_bytes(), f"Admin: add image {local_path.name}", branch)

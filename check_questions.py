import sqlite3, json, random

random.seed(777)

bk_conn = sqlite3.connect(r'C:\Users\Razvan\Documents\Radiologie\backups\edir_prep.db')
bk_conn.row_factory = sqlite3.Row
bk_cur = bk_conn.cursor()

live_conn = sqlite3.connect('data/edir_prep.db')
live_conn.row_factory = sqlite3.Row
lv_cur = live_conn.cursor()

SEC = 'mrq'
SRC = 'Core Radiology'

for case_num in [2, 3, 4, 5]:
    lv_cur.execute(
        "SELECT q.q_number, q.options, a.correct_options, a.explanation "
        "FROM questions q JOIN cases c ON c.id=q.case_id JOIN answers a ON a.question_id=q.id "
        "WHERE c.chapter_id=5 AND c.section=? AND c.source=? AND c.case_number=? "
        "ORDER BY q.q_number",
        (SEC, SRC, case_num)
    )
    lv_rows = lv_cur.fetchall()

    bk_cur.execute(
        "SELECT q.q_number, q.options, a.explanation "
        "FROM questions q JOIN cases c ON c.id=q.case_id JOIN answers a ON a.question_id=q.id "
        "WHERE c.chapter_id=5 AND c.section=? AND c.source=? AND c.case_number=? "
        "ORDER BY q.q_number",
        (SEC, SRC, case_num)
    )
    bk_rows = bk_cur.fetchall()

    picks = random.sample(range(len(lv_rows)), 3)
    print(f'=== CASE {case_num} ===')
    for idx in sorted(picks):
        lv = lv_rows[idx]
        bk_r = bk_rows[idx]
        opts = json.loads(lv['options'])
        correct_idx = json.loads(lv['correct_options'])
        correct_letters = [chr(ord('a') + i) for i in correct_idx]

        print(f'  Q{lv["q_number"]}  correct={correct_idx} -> {correct_letters}')
        for i, o in enumerate(opts):
            marker = '<CORRECT>' if i in correct_idx else '         '
            safe = o[:85].encode('ascii', errors='replace').decode()
            print(f'    {marker} {chr(ord("a") + i)}. {safe}')
        live_e = lv['explanation'].encode('ascii', errors='replace').decode()
        back_e = bk_r['explanation'].encode('ascii', errors='replace').decode()
        print(f'  LIVE:   {live_e}')
        print(f'  BACKUP: {back_e}')
        print()

bk_conn.close()
live_conn.close()

"""查看 .langgraph.db 中的 Checkpoint 数据"""

import sqlite3
import json

DB_PATH = ".langgraph.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("=" * 60)
print("数据库表结构")
print("=" * 60)
for t in tables:
    print(f"  📦 {t[0]}")

# 查看 checkpoints 表
print("\n" + "=" * 60)
print("Checkpoint 概览")
print("=" * 60)

try:
    cursor.execute("""
        SELECT thread_id, checkpoint_id, 
               length(checkpoint) as size_bytes,
               length(metadata) as meta_bytes
        FROM checkpoints 
        ORDER BY thread_id, checkpoint_id
    """)
    rows = cursor.fetchall()

    if not rows:
        print("  (暂无数据 — 先跑几轮对话后再看)")
    else:
        current_thread = None
        for row in rows:
            thread_id, cp_id, size, meta = row
            if thread_id != current_thread:
                print(f"\n  🧵 thread_id: {thread_id}")
                current_thread = thread_id
            print(f"     ├─ {cp_id[:12]}... ({size}B)")

        print(f"\n  共 {len(rows)} 个检查点，{len(set(r[0] for r in rows))} 个会话")

except sqlite3.OperationalError as e:
    print(f"  表结构可能不同: {e}")

conn.close()

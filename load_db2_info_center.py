import json
from sqlalchemy import create_engine, text

DB2_HOST = "localhost"
DB2_PORT = 50050
DB2_DATABASE = "dbcdw"
DB2_USER = "db2inst1"
DB2_PASSWORD = "Babalu07"
CONNECTION_STRING = f"ibm_db_sa://{DB2_USER}:{DB2_PASSWORD}@{DB2_HOST}:{DB2_PORT}/{DB2_DATABASE}"

engine = create_engine(CONNECTION_STRING)

chunks = []
with open('/tmp/opencode/db2_info_center_chunks.jsonl', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            chunks.append(json.loads(line))

with engine.begin() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE DB2_INFO_CENTER (
                CHUNK_ID VARCHAR(64) NOT NULL PRIMARY KEY,
                DOC_ID VARCHAR(128),
                SOURCE VARCHAR(1024),
                PAGE_NUM INTEGER,
                CHUNK_INDEX INTEGER,
                CHUNK_TEXT CLOB(2M)
            )
        """))
        print('created')
    except Exception as e:
        print('create skipped:', str(e)[:120])
    # clear existing for this doc
    conn.execute(text("DELETE FROM DB2_INFO_CENTER WHERE DOC_ID = :d"), {"d": "db2_sys_mon_guide_1213"})
    # batch insert
    stmt = text("INSERT INTO DB2_INFO_CENTER (CHUNK_ID,DOC_ID,SOURCE,PAGE_NUM,CHUNK_INDEX,CHUNK_TEXT) VALUES (:chunk_id,:doc_id,:source,:page_num,:chunk_index,:text)")
    batch = 200
    for i in range(0, len(chunks), batch):
        conn.execute(stmt, chunks[i:i+batch])
        print('inserted up to', min(i+batch, len(chunks)))
with engine.connect() as conn:
    n = conn.execute(text("SELECT COUNT(*) AS CNT FROM DB2_INFO_CENTER")).scalar()
    print('total', n)

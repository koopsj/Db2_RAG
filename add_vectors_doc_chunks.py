#!/usr/bin/env python3
import os, sys, time
from sentence_transformers import SentenceTransformer
import ibm_db_dbi

host=os.getenv('DB2_HOST','localhost'); port=os.getenv('DB2_PORT','50050')
db=os.getenv('DB2_DATABASE','dbcdw'); user=os.getenv('DB2_USER','db2inst1')
pwd=os.getenv('DB2_PASSWORD','Babalu07')
dsn = f"DATABASE={db};HOSTNAME={host};PORT={port};PROTOCOL=TCPIP;UID={user};PWD={pwd};"
conn = ibm_db_dbi.connect(dsn, "", "")
cur = conn.cursor()

print("Loading model...")
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
cur.execute("SELECT CHUNK_ID, CAST(CHUNK_TEXT AS VARCHAR(8000)) AS TXT FROM DB2INST1.DOCUMENT_CHUNKS_PDF WHERE EMBEDDING IS NULL ORDER BY CHUNK_ID")
rows = cur.fetchall()
print(f"Rows: {len(rows)}")
upd_tpl = "UPDATE DB2INST1.DOCUMENT_CHUNKS_PDF SET EMBEDDING = VECTOR('{vstr}', 384, FLOAT32) WHERE CHUNK_ID = ?"
for i in range(0, len(rows), 32):
    batch = rows[i:i+32]
    ids=[r[0] for r in batch]; texts=[(r[1] or '') for r in batch]
    embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    for cid, vec in zip(ids, embs):
        vstr = "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"
        cur.execute(upd_tpl.format(vstr=vstr), (cid,))
    conn.commit()
    print(f"Updated {min(i+32,len(rows))}/{len(rows)}")
print("Done")

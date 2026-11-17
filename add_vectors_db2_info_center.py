#!/usr/bin/env python3
"""
Generate embeddings for DB2INST1.DB2_INFO_CENTER.CHUNK_TEXT and store in EMBEDDING VECTOR column.

Usage:
  python add_vectors_db2_info_center.py [--batch 64] [--model sentence-transformers/all-MiniLM-L6-v2] [--limit N]
Env/connection defaults match the local db2-server setup; override with DB2_* vars if needed.
"""
import argparse, os, sys, time
import numpy as np
import ibm_db
import ibm_db_dbi
from sentence_transformers import SentenceTransformer

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--batch', type=int, default=64)
    ap.add_argument('--model', default='sentence-transformers/all-MiniLM-L6-v2')
    ap.add_argument('--limit', type=int, default=0)
    ap.add_argument('--offset', type=int, default=0)
    args = ap.parse_args()

    host=os.getenv('DB2_HOST','localhost'); port=os.getenv('DB2_PORT','50050')
    db=os.getenv('DB2_DATABASE','dbcdw'); user=os.getenv('DB2_USER','db2inst1')
    pwd=os.getenv('DB2_PASSWORD','Babalu07')
    dsn = f"DATABASE={db};HOSTNAME={host};PORT={port};PROTOCOL=TCPIP;UID={user};PWD={pwd};"
    conn = ibm_db_dbi.connect(dsn, "", "")
    cur = conn.cursor()

    print(f"Loading model {args.model}...")
    model = SentenceTransformer(args.model)
    dim = model.get_sentence_embedding_dimension()
    print(f"Embedding dimension: {dim}")

    # fetch rows missing embedding
    q = "SELECT CHUNK_ID, CAST(CHUNK_TEXT AS VARCHAR(8000)) AS TXT FROM DB2INST1.DB2_INFO_CENTER WHERE EMBEDDING IS NULL ORDER BY CHUNK_ID"
    if args.limit: q += f" FETCH FIRST {args.limit} ROWS ONLY"
    cur.execute(q)
    rows = cur.fetchall()
    print(f"Rows to embed: {len(rows)}")
    if not rows:
        return 0

    upd_tpl = "UPDATE DB2INST1.DB2_INFO_CENTER SET EMBEDDING = VECTOR('{vstr}', 384, FLOAT32) WHERE CHUNK_ID = ?"
    total = 0; t0=time.time()
    for i in range(0, len(rows), args.batch):
        batch = rows[i:i+args.batch]
        ids = [r[0] for r in batch]
        texts = [(r[1] or "") for r in batch]
        embs = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        for cid, vec in zip(ids, embs):
            vstr = "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"
            cur.execute(upd_tpl.format(vstr=vstr), (cid,))
        conn.commit()
        total += len(batch)
        if total % 512 == 0 or i+args.batch >= len(rows):
            elapsed=time.time()-t0; rate=total/elapsed if elapsed>0 else 0
            print(f"Updated {total}/{len(rows)} ({rate:.1f} rows/s)")
    print(f"Done. Updated {total} rows in {time.time()-t0:.1f}s")
    return 0

if __name__ == '__main__':
    sys.exit(main())

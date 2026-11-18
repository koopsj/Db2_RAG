#!/usr/bin/env python3
"""Query Db2 RAG (Ollama-embedded, local) with cleaner, readable output."""
import json
import re
import sys
import textwrap
import urllib.request
import ibm_db_dbi

TABLE = "DB2INST1.DB2_RAG_CHUNKS_OLLAMA"
DB = "DATABASE=dbcdw;HOSTNAME=localhost;PORT=50050;PROTOCOL=TCPIP;UID=db2inst1;PWD=Babalu07;"
OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "all-minilm"
TOP_K = 5

def clean_snippet(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"\s+", " ", text).strip()
    return text

def main():
    if len(sys.argv) < 2:
        print('Usage: python query_rag_ollama_clean.py "<question>" [top_k]')
        sys.exit(1)
    question = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_K

    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({"model": OLLAMA_MODEL, "input": question}).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=120) as r:
        vec = json.load(r)["embeddings"][0]
    qvec = "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

    conn = ibm_db_dbi.connect(DB, "", "")
    cur = conn.cursor()
    sql = f"""
    SELECT CHUNK_ID, DOC_ID, PAGE_NUM, CHUNK_INDEX,
           CAST(CHUNK_TEXT AS VARCHAR(3000)) AS TEXT_SNIPPET,
           VECTOR_DISTANCE(EMBEDDING, VECTOR('{qvec}', 384, FLOAT32), COSINE) AS dist
    FROM {TABLE}
    WHERE EMBEDDING IS NOT NULL
    ORDER BY dist
    FETCH FIRST {top_k} ROWS ONLY
    """
    cur.execute(sql)
    rows = cur.fetchall()
    print(f"\nQuestion: {question}")
    print(f"Top {len(rows)} results from {TABLE}\n" + "=" * 88)
    for i, r in enumerate(rows, 1):
        snippet = clean_snippet(r[4] or "")
        wrapped = textwrap.fill(snippet, width=100)
        print(f"[{i}] doc={r[1]}  page={r[2]}  chunk={r[3]}  dist={float(r[5]):.6f}")
        print(f"    id={r[0]}")
        print(textwrap.indent(wrapped, "    "))
        print("-" * 88)

if __name__ == "__main__":
    main()

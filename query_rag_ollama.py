import json
import sys
import urllib.request
import ibm_db_dbi

if len(sys.argv) < 2:
    print("Usage: python query_rag_ollama.py \"<question>\"")
    sys.exit(1)

question = sys.argv[1]
OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "all-minilm"  # 384-dim, matches DB2_INST1.* EMBEDDING VECTOR(384,FLOAT32)

# 1) Generate query embedding locally via Ollama
req = urllib.request.Request(
    OLLAMA_URL,
    data=json.dumps({"model": OLLAMA_MODEL, "input": question}).encode(),
    headers={"Content-Type": "application/json"},
)
with urllib.request.urlopen(req) as r:
    data = json.load(r)
vec = data["embeddings"][0]
qvec = "[" + ",".join(f"{float(x):.8f}" for x in vec) + "]"

# 2) Semantic search in Db2
conn = ibm_db_dbi.connect(
    "DATABASE=dbcdw;HOSTNAME=localhost;PORT=50050;PROTOCOL=TCPIP;UID=db2inst1;PWD=<password>;",
    "", "",
)
cur = conn.cursor()
sql = f"""
SELECT CHUNK_ID, DOC_ID, PAGE_NUM,
       SUBSTR(CAST(CHUNK_TEXT AS VARCHAR(2500)),1,2500) AS TEXT_SNIPPET,
       VECTOR_DISTANCE(EMBEDDING, VECTOR('{qvec}', 384, FLOAT32), COSINE) AS dist
FROM DB2INST1.DB2_INFO_CENTER
WHERE EMBEDDING IS NOT NULL
ORDER BY dist
FETCH FIRST 8 ROWS ONLY
"""
cur.execute(sql)
for row in cur.fetchall():
    print(row[1], row[0], "p." + str(row[2]), "dist=", row[4])
    print(row[3][:800], "...\n")

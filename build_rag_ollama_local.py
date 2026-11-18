#!/usr/bin/env python3
"""
Complete local Db2 RAG setup (from scratch):
- Extract text from local PDF files (PyMuPDF)
- Clean and split into smaller, sentence-aware chunks (inline-friendly VARCHAR)
- Generate embeddings locally via Ollama (all-minilm, 384-dim)
- Load into Db2 table DB2INST1.DB2_RAG_CHUNKS_OLLAMA

Requirements: local PDFs, Ollama running with pulled embedding model, pymupdf, ibm_db_dbi.
"""
import glob
import json
import os
import re
import sys
import time
import urllib.request

import ibm_db_dbi

try:
    import fitz  # PyMuPDF
except Exception as e:
    print(f"ERROR: PyMuPDF (fitz/pymupdf) not available: {e}", file=sys.stderr)
    sys.exit(2)

# --- Config (adjust as needed) ---
PDF_DIR = "/tmp/opencode/db2_manuals"
TABLE = "DB2INST1.DB2_RAG_CHUNKS_OLLAMA"
DB = "DATABASE=dbcdw;HOSTNAME=localhost;PORT=50050;PROTOCOL=TCPIP;UID=db2inst1;PWD=Babalu07;"
OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "all-minilm"
EMBED_DIM = 384
EMBED_BATCH = 32
CHUNK_TARGET = 500      # preferred chunk size (chars)
CHUNK_MAX = 900         # hard max (kept << VARCHAR(3000) for inline storage)
CHUNK_MIN = 120         # avoid tiny fragments (merge when possible)
# ----------------------------------

def warn(msg):
    print(f"WARNING: {msg}", flush=True)

def clean_text(text: str) -> str:
    if not text:
        return ""
    # de-hyphenate line-break splits: "configu-\nration" -> "configuration"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # normalize newlines/tabs to spaces but keep paragraph hints
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    # collapse excessive blank lines, keep single paragraph breaks as space marker
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n", " ", text)
    # remove non-printable/control chars except common punctuation context
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
    text = re.sub(r"\s{2,}", " ", text).strip()
    return text

def split_sentences(text: str):
    # simple sentence-aware split keeping delimiters
    parts = re.split(r'(?<=[\.!\?\:;])\s+(?=[A-Z0-9"(\[])', text)
    return [p.strip() for p in parts if p and p.strip()]

def chunk_text(text: str, target=CHUNK_TARGET, maxlen=CHUNK_MAX, minlen=CHUNK_MIN):
    text = clean_text(text)
    if not text:
        return []
    sents = split_sentences(text)
    if not sents:
        sents = [text]
    chunks = []
    cur = ""
    for s in sents:
        if not cur:
            cur = s
            continue
        if len(cur) + 1 + len(s) <= target:
            cur = cur + " " + s
        elif len(cur) >= minlen:
            chunks.append(cur.strip())
            cur = s
        elif len(cur) + 1 + len(s) <= maxlen:
            cur = cur + " " + s
        else:
            chunks.append(cur.strip())
            cur = s
        # hard split if a single sentence/segment is too long
        while len(cur) > maxlen:
            cut = cur.rfind(" ", 0, maxlen)
            if cut < int(maxlen * 0.6):
                cut = maxlen
            chunks.append(cur[:cut].strip())
            cur = cur[cut:].strip()
    if cur:
        if chunks and len(cur) < minlen and len(chunks[-1]) + 1 + len(cur) <= maxlen:
            chunks[-1] = (chunks[-1] + " " + cur).strip()
        else:
            chunks.append(cur.strip())
    # final safety trim
    out = []
    for c in chunks:
        c = c.strip()
        if len(c) > maxlen:
            c = c[:maxlen].rsplit(" ", 1)[0].strip() or c[:maxlen]
        if c:
            out.append(c)
    return out

def get_embeddings(texts):
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps({"model": OLLAMA_MODEL, "input": texts}).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = json.load(r)
    except Exception as e:
        raise RuntimeError(f"Ollama embedding request failed: {e}")
    embs = data.get("embeddings")
    if not embs or len(embs) != len(texts):
        raise RuntimeError(f"Unexpected embedding response shape: {type(embs)} len={len(embs) if embs else None}")
    if len(embs[0]) != EMBED_DIM:
        raise RuntimeError(f"Embedding dim {len(embs[0])} != expected {EMBED_DIM}")
    return embs

def main():
    # preflight checks
    pdfs = sorted(glob.glob(os.path.join(PDF_DIR, "*.pdf")))
    if not pdfs:
        print(f"ERROR: no PDF files found in {PDF_DIR}. Local PDF split not possible.", file=sys.stderr)
        sys.exit(2)
    try:
        with urllib.request.urlopen(urllib.request.Request(OLLAMA_URL, data=json.dumps({"model":OLLAMA_MODEL,"input":"ping"}).encode(), headers={"Content-Type":"application/json"}), timeout=30) as r:
            d = json.load(r)
            if len(d["embeddings"][0]) != EMBED_DIM:
                warn(f"model dim {len(d['embeddings'][0])} differs from {EMBED_DIM}")
    except Exception as e:
        print(f"ERROR: Ollama not reachable or model '{OLLAMA_MODEL}' unavailable at {OLLAMA_URL}: {e}", file=sys.stderr)
        print("Ensure Ollama is running and run: ollama pull " + OLLAMA_MODEL, file=sys.stderr)
        sys.exit(2)

    conn = ibm_db_dbi.connect(DB, "", "")
    conn.autocommit = False
    cur = conn.cursor()

    total_chunks = 0
    total_docs = 0
    for pdf in pdfs:
        doc_id = os.path.splitext(os.path.basename(pdf))[0]
        # resumable: skip doc if already fully loaded
        cur.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE DOC_ID = ?", (doc_id,))
        if cur.fetchone()[0] > 0:
            print(f"skip {doc_id} (already loaded)", flush=True)
            continue
        try:
            doc = fitz.open(pdf)
        except Exception as e:
            warn(f"cannot open {pdf}: {e}")
            continue
        print(f"processing {doc_id} pages={doc.page_count}", flush=True)
        # collect chunks per doc
        doc_chunks = []  # (page_num, chunk_index, text)
        for pno in range(doc.page_count):
            try:
                text = doc[pno].get_text("text") or ""
            except Exception as e:
                warn(f"{doc_id} page {pno+1} extract failed: {e}")
                text = ""
            cks = chunk_text(text)
            for ci, ct in enumerate(cks):
                doc_chunks.append((pno + 1, ci, ct))
        doc.close()
        if not doc_chunks:
            warn(f"{doc_id}: no text chunks extracted")
            continue
        # embed + insert in batches
        ins = conn.cursor()
        inserted = 0
        for i in range(0, len(doc_chunks), EMBED_BATCH):
            batch = doc_chunks[i:i+EMBED_BATCH]
            texts = [b[2] for b in batch]
            embs = None
            for attempt in range(3):
                try:
                    embs = get_embeddings(texts)
                    break
                except Exception as e:
                    if attempt == 2:
                        raise
                    warn(f"embed retry {attempt+1} for {doc_id}: {e}")
                    time.sleep(2)
            for j, (page_num, chunk_index, ctext) in enumerate(batch):
                # global sequential chunk_index per doc in insertion order
                seq = i + j
                chunk_id = f"{doc_id}::{seq}"
                qvec = "[" + ",".join(f"{float(x):.8f}" for x in embs[j]) + "]"
                ins.execute(
                    f"INSERT INTO {TABLE} (CHUNK_ID,DOC_ID,SOURCE,PAGE_NUM,CHUNK_INDEX,CHUNK_TEXT,EMBEDDING) "
                    "VALUES (?,?,?,?,?,?, VECTOR(?,384,FLOAT32))",
                    (chunk_id, doc_id, pdf, page_num, seq, ctext, qvec),
                )
            conn.commit()
            inserted += len(batch)
            if inserted % 256 == 0 or inserted == len(doc_chunks):
                print(f"  {doc_id}: {inserted}/{len(doc_chunks)} chunks", flush=True)
        total_chunks += inserted
        total_docs += 1
        print(f"done {doc_id}: chunks={inserted}", flush=True)

    print(f"ALL DONE docs={total_docs} chunks={total_chunks}", flush=True)

if __name__ == "__main__":
    main()

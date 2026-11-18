# Db2 RAG – Complete Local Setup (Ollama embeddings, from scratch)

This document describes a **complete, local-from-scratch** setup of a Db2 Retrieval-Augmented Generation (RAG) store using:
- **Local PDF extraction & chunking** (PyMuPDF)
- **Local embedding generation** via **Ollama** (`all-minilm`, 384-dim)
- **IBM Db2** storage with `VECTOR` and similarity search via `VECTOR_DISTANCE`

It replaces earlier "copy-from-existing-chunks" experiments with a clean pipeline optimized for **smaller, sentence-aware chunks**, **cleaner text**, and **inline-friendly column storage** (reduced I/O).

> **Status (this run):** table `DB2INST1.DB2_RAG_CHUNKS_OLLAMA` created and ingestion started from local PDFs in `/tmp/opencode/db2_manuals/` using the scripts below. Monitor until complete (see §6). If any prerequisite is missing (local PDFs, Ollama/model, Db2 access, Python libs), the scripts emit explicit errors/warnings and stop as appropriate.

---

## 1. Goals & design choices

### 1.1 Why smaller, precise chunks
- **No mid-sentence/semantic cuts where avoidable:** sentence/paragraph-aware splitting keeps chunks readable and self-contained.
- **Smaller blocks:** target ~500 chars (max ~900) instead of ~900–1200+ chars.
- **Cleaner text:** de-hyphenation of line breaks, whitespace/control-char normalization for better readability and embedding quality.
- **Inline-friendly storage / lower I/O:** `CHUNK_TEXT` stored as `VARCHAR(3000)` (not `CLOB`) so small values can be inlined in Db2 data pages, reducing LOB I/O and improving scan/query performance. (No vector index used; `VECTOR` indexing was not supported in this environment — see §7.)

### 1.2 Local-only processing
- **PDF split/extraction:** performed locally with PyMuPDF (`fitz`) from local PDF files.
- **Embeddings:** generated locally via Ollama HTTP API (`all-minilm`, 384-dim). No remote embedding service; no Python embedding-model download required at query/build time beyond the local Ollama model.
- **Warning behavior:** scripts fail fast with clear messages if local PDFs are missing, Ollama/model is unavailable, or required libraries are missing.

### 1.3 Components
| Component | Value |
|---|---|
| Db2 | `dbcdw` @ `localhost:50050`, user `db2inst1`, Db2 v12.1.5.0 (VECTOR available) |
| Table | `DB2INST1.DB2_RAG_CHUNKS_OLLAMA` |
| Embedding model | Ollama `all-minilm` (`bert`, 23M, F16, 384-dim) |
| Distance | `VECTOR_DISTANCE(..., COSINE)` |
| PDF source (local) | `/tmp/opencode/db2_manuals/*.pdf` (21 Db2 manuals, cached locally) |
| Python (Db2+pymupdf) | `/home/jkoops/pyenv/bin/python` (`ibm_db_dbi`, `pymupdf/fitz`) |

---

## 2. Prerequisites (all local) & verification

1. **Db2 reachable with write/DDL** (e.g. via `db2-server` MCP with `DB2_ALLOW_WRITE=1`, or direct client).
2. **Ollama installed and running**:
   ```bash
   ollama --version
   curl -s http://localhost:11434/api/tags
   ```
3. **Embedding model pulled locally**:
   ```bash
   ollama pull all-minilm
   ollama list   # should show all-minilm:latest
   ```
4. **Verify embedding API & dimension (expect 384)**:
   ```bash
   curl -s http://localhost:11434/api/embed -d '{"model":"all-minilm","input":"ping"}' \
     | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d['embeddings'][0]))"
   # 384
   ```
5. **Local PDFs present** (no network download required if cached):
   ```bash
   ls /tmp/opencode/db2_manuals/*.pdf | wc -l   # expected 21
   ```
   > If PDFs are missing, obtain/place them locally under `/tmp/opencode/db2_manuals/` before running ingestion (the build script warns and exits).
6. **Python dependencies** (local):
   ```bash
   /home/jkoops/pyenv/bin/python -c "import fitz, ibm_db_dbi, json, re; print('ok')"
   ```

---

## 3. Schema (inline-friendly, smaller chunks)

```sql
CREATE TABLE DB2INST1.DB2_RAG_CHUNKS_OLLAMA (
  CHUNK_ID    VARCHAR(128)  NOT NULL PRIMARY KEY,  -- "{doc_id}::{seq}"
  DOC_ID      VARCHAR(256)  NOT NULL,
  SOURCE      VARCHAR(1024) NOT NULL,              -- local PDF path
  PAGE_NUM    INTEGER       NOT NULL,
  CHUNK_INDEX INTEGER       NOT NULL,              -- sequential per document
  CHUNK_TEXT  VARCHAR(3000) NOT NULL,              -- cleaned, sentence-aware, small (inline-friendly)
  EMBEDDING   VECTOR(384, FLOAT32)                 -- Ollama all-minilm
);
```

**Rationale:** chunks target ~500 chars (max ~900) so `CHUNK_TEXT` stays well within `VARCHAR(3000)` and can be stored inline (less LOB/row overflow I/O) while remaining precise and readable.

*(Recreate/clean start: `DROP TABLE DB2INST1.DB2_RAG_CHUNKS_OLLAMA;` then `CREATE ...` as above.)*

---

## 4. Scripts (all steps run locally)

### 4.1 Build/ingest script: extract + clean + precise chunk + Ollama embed + load
**File:** `/tmp/opencode/build_rag_ollama_local.py` (executable)

What it does (per PDF, resumable by `DOC_ID`):
1. **Extract** text page-by-page locally (`pymupdf`, `page.get_text("text")`).
2. **Clean**: de-hyphenate line-break splits, normalize whitespace/newlines/control chars.
3. **Split precisely**: sentence-aware chunking with paragraph/sentence preference, target ~500 chars, hard max ~900, min ~120 (avoids tiny fragments and mid-sentence cuts where possible).
4. **Embed locally**: batch calls to Ollama `POST /api/embed` (`model=all-minilm`, 384-dim), with retry.
5. **Load to Db2**: `INSERT` `(CHUNK_ID,DOC_ID,SOURCE,PAGE_NUM,CHUNK_INDEX,CHUNK_TEXT,EMBEDDING VECTOR(...))`, commit per batch. Skips docs already present (safe to rerun).

Key configuration (inside script):
```python
PDF_DIR = "/tmp/opencode/db2_manuals"
TABLE = "DB2INST1.DB2_RAG_CHUNKS_OLLAMA"
OLLAMA_URL = "http://localhost:11434/api/embed"
OLLAMA_MODEL = "all-minilm"      # 384-dim
CHUNK_TARGET = 500; CHUNK_MAX = 900; CHUNK_MIN = 120
EMBED_BATCH = 32
```

Run:
```bash
/home/jkoops/pyenv/bin/python -u /tmp/opencode/build_rag_ollama_local.py 2>&1 | tee /tmp/opencode/build_rag_ollama_local.log
# or background/resumable:
# nohup /home/jkoops/pyenv/bin/python -u /tmp/opencode/build_rag_ollama_local.py > /tmp/opencode/build_rag_ollama_local.log 2>&1 &
```

Preflight behavior (local checks): errors/exits if no PDFs found, if Ollama/model unreachable, or if required libs missing; warnings on per-page/per-doc issues with retries for embedding.

### 4.2 Query script (clean, readable output)
**File:** `/tmp/opencode/query_rag_ollama_clean.py` (executable)

- Embeds the question locally via Ollama (`all-minilm`, 384-dim).
- Runs `VECTOR_DISTANCE(EMBEDDING, VECTOR('<qvec>',384,FLOAT32), COSINE)` against `DB2INST1.DB2_RAG_CHUNKS_OLLAMA`.
- Prints ranked results with `doc/page/chunk/dist/id` and **normalized/wrapped snippets** for cleaner reading.

Run:
```bash
/home/jkoops/pyenv/bin/python /tmp/opencode/query_rag_ollama_clean.py "How to configure JWT authentication in Db2?" [top_k]
```

---

## 5. End-to-end run log (steps executed)

1. Verified Ollama running with `all-minilm` (384-dim, embedding): `curl /api/tags`, `curl /api/embed`.
2. Verified local PDFs: `ls /tmp/opencode/db2_manuals/*.pdf` → 21 manuals.
3. Verified Python deps: `/home/jkoops/pyenv/bin/python -c "import fitz, ibm_db_dbi"`.
4. Recreated target table for clean, inline-friendly schema:
   ```sql
   DROP TABLE DB2INST1.DB2_RAG_CHUNKS_OLLAMA;  -- removed prior copy-based experiment
   CREATE TABLE DB2INST1.DB2_RAG_CHUNKS_OLLAMA (... CHUNK_TEXT VARCHAR(3000) ..., EMBEDDING VECTOR(384,FLOAT32));
   ```
5. Started local ingestion (extract+clean+chunk+embed+load):
   ```bash
   nohup /home/jkoops/pyenv/bin/python -u /tmp/opencode/build_rag_ollama_local.py > /tmp/opencode/build_rag_ollama_local.log 2>&1 &
   ```
6. Monitor progress:
   ```bash
   tail -f /tmp/opencode/build_rag_ollama_local.log
   ```
   ```sql
   SELECT COUNT(*) AS chunks, COUNT(DISTINCT DOC_ID) AS docs
   FROM DB2INST1.DB2_RAG_CHUNKS_OLLAMA;
   ```

> **Note:** Full embedding of all manuals is CPU/time intensive (tens of thousands of chunks). The build is **resumable** (skips already-loaded `DOC_ID`s); rerun safely until all local PDFs are loaded.

---

## 6. Validation / completion checks

```sql
-- coverage
SELECT COUNT(*) AS chunks,
       COUNT(DISTINCT DOC_ID) AS docs,
       SUM(CASE WHEN EMBEDDING IS NOT NULL THEN 1 ELSE 0 END) AS embedded
FROM DB2INST1.DB2_RAG_CHUNKS_OLLAMA;

-- chunk size sanity (should be small/inline-friendly)
SELECT MIN(LENGTH(CHUNK_TEXT)) AS min_len,
       AVG(LENGTH(CHUNK_TEXT)) AS avg_len,
       MAX(LENGTH(CHUNK_TEXT)) AS max_len
FROM DB2INST1.DB2_RAG_CHUNKS_OLLAMA;

-- sample
SELECT CHUNK_ID, DOC_ID, PAGE_NUM, CHUNK_INDEX,
       SUBSTR(CAST(CHUNK_TEXT AS VARCHAR(300)),1,300) AS SNIP
FROM DB2INST1.DB2_RAG_CHUNKS_OLLAMA FETCH FIRST 5 ROWS ONLY;
```

---

## 7. Query examples (Db2 RAG with vectors)

All examples: **embed the question locally** with Ollama `all-minilm` (384-dim), then rank by `VECTOR_DISTANCE(..., COSINE)` over `EMBEDDING IS NOT NULL`. Use the clean script for readable output:
```bash
/home/jkoops/pyenv/bin/python /tmp/opencode/query_rag_ollama_clean.py "<question>" 5
```

### Example 1 — Configure JWT authentication
```bash
/home/jkoops/pyenv/bin/python /tmp/opencode/query_rag_ollama_clean.py \
  "How to configure JWT authentication in Db2 (db2token.cfg, issuer, JWKS/certificate, and client connection)?"
```
**What to expect:** top chunks from the security guide covering `db2token.cfg` (`VERSION`, `TOKEN_TYPES_SUPPORTED=JWT`, `JWT_KEYDB`, `JWT_IDP_ISSUER`, `JWT_IDP_AUTHID_CLAIM`, key/cert labels/algorithms) and client usage (`accesstoken`/`accesstokentype jwt` via CLP/CLI/JDBC). Cite `DOC_ID, PAGE_NUM, CHUNK_ID` in answers.

### Example 2 — Configure SSL/TLS for the Db2 server
```bash
/home/jkoops/pyenv/bin/python /tmp/opencode/query_rag_ollama_clean.py \
  "How to configure SSL TLS on the Db2 server (keystore, certificate, SSL_SVR_KEYDB, SSL_SVCENAME, DB2COMM)?"
```
**What to expect:** chunks describing keystore/certificate setup (GSKit), `SSL_SVR_KEYDB/SSL_SVR_STASH/SSL_SVR_LABEL`, `SSL_SVCENAME` (and optional `SSL_VERSIONS`/`SSL_CIPHERSPECS`), setting `DB2COMM` to SSL/TCPIP, and restarting the instance.

### Example 3 — Set up WLM (service class, workload, activity collection)
```bash
/home/jkoops/pyenv/bin/python /tmp/opencode/query_rag_ollama_clean.py \
  "How to set up Db2 Workload Manager: create service class and workload and collect activity data?"
```
**What to expect:** chunks related to `CREATE SERVICE CLASS` / `CREATE WORKLOAD`, workload attributes/mapping, and collecting activity/aggregate data (e.g. `COLLECT ACTIVITY DATA`, `COLLECT AGGREGATE ACTIVITY DATA`) from WLM/admin/performance manuals.

**Equivalent SQL (template, with `<qvec>` generated locally by Ollama):**
```sql
SELECT CHUNK_ID, DOC_ID, PAGE_NUM, CHUNK_INDEX,
       CAST(CHUNK_TEXT AS VARCHAR(3000)) AS TEXT_SNIPPET,
       VECTOR_DISTANCE(EMBEDDING, VECTOR('<qvec>', 384, FLOAT32), COSINE) AS dist
FROM DB2INST1.DB2_RAG_CHUNKS_OLLAMA
WHERE EMBEDDING IS NOT NULL
ORDER BY dist
FETCH FIRST 5 ROWS ONLY;
```

---

## 8. Operational notes & limitations
- **Resumability:** build script skips `DOC_ID`s already loaded; rerun to continue after interruption. To fully rebuild, drop/recreate the table.
- **Vector index:** not created (`VECTOR` not indexable in this environment; e.g. `SQL0350N`/`SQLSTATE 42962`). Retrieval is scan-based via `VECTOR_DISTANCE`; prefilter by `DOC_ID`/keywords when possible.
- **Model/dimension consistency:** query embeddings must use the **same** model/dim/normalization as stored (`all-minilm`, 384). Changing models requires a new vector column/table and re-embedding.
- **Scanned/image-only PDFs:** this pipeline uses text extraction (`get_text("text")`); scanned PDFs need OCR (e.g. Tesseract) as a pre-step — add OCR if such sources are required (script will warn/produce few chunks if text is absent).
- **Security:** protect Db2 credentials; keep Ollama bound appropriately (local). Do not commit secrets.
- **Legacy tables:** `DB2INST1.DB2_INFO_CENTER` / `DOCUMENT_CHUNKS_PDF` (sentence-transformers, larger/CLOB chunks) remain untouched for comparison/fallback.

---

## 9. Artifacts produced
- `/tmp/opencode/build_rag_ollama_local.py` – local PDF extract/clean/chunk + Ollama embed + Db2 load (from scratch, resumable)
- `/tmp/opencode/query_rag_ollama_clean.py` – semantic query with clean, wrapped output
- `/tmp/opencode/build_rag_ollama_local.log` – ingestion log (when run)
- Db2 table: `DB2INST1.DB2_RAG_CHUNKS_OLLAMA (CHUNK_ID, DOC_ID, SOURCE, PAGE_NUM, CHUNK_INDEX, CHUNK_TEXT VARCHAR(3000), EMBEDDING VECTOR(384,FLOAT32))`
- Local inputs: `/tmp/opencode/db2_manuals/*.pdf`, Ollama model `all-minilm`

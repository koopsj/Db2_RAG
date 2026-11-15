# Db2 Documentation RAG Setup (using `db2-server` MCP)

This document captures the **prompt**, **steps**, and **artifacts** used to set up a text-based RAG knowledge store in IBM Db2 from PDF documents (including IBM Db2 manuals), and to query it via the OpenCode `db2-server` MCP.

> **Scope/limitations:** This setup loads **text + metadata** chunks into Db2 (`CHUNK_TEXT`). It does **not** generate/store embeddings or a `VECTOR` column. For full vector similarity RAG, add an embedding step/model and a vector column/index supported by your Db2 version.

---

## 1. Goal
- Store PDF content as retrievable chunks in Db2.
- Query the stored documentation via `db2-server` MCP to answer questions (e.g. monitor elements, SSL/TLS configuration) from the loaded Db2 manuals.
- Optionally bulk-load IBM Db2 12.1 LUW English manuals.

**Target table (same schema used):** `DB2INST1.DB2_INFO_CENTER` (and example `DB2INST1.DOCUMENT_CHUNKS_PDF`)

| Column | Type | Notes |
|---|---|---|
| `CHUNK_ID` | `VARCHAR(64/128)` | Primary key |
| `DOC_ID` | `VARCHAR(128/256)` | Document identifier |
| `SOURCE` | `VARCHAR(1024/2048)` | Source path/URL |
| `PAGE_NUM` | `INTEGER` | Page number |
| `CHUNK_INDEX` | `INTEGER` | Chunk index within page |
| `CHUNK_TEXT` | `CLOB(2M)` | Extracted text chunk |

---

## 2. Prerequisites
- Access to OpenCode with the **`db2-server` MCP** configured and connected to a Db2 instance.
- Db2 credentials/instance reachable by the MCP server (example connection used by the server: `ibm_db_sa://db2inst1:***@localhost:50050/dbcdw`).
- Local filesystem access to PDFs (e.g. `/home/jkoops/pdfs/`).
- Tools/libraries for extraction & loading:
  - Python venv (example: `/tmp/opencode/ragvenv`) with `pymupdf` (`fitz`), `pytesseract`, `pillow` for OCR; system `tesseract`, `poppler-utils` for scanned PDFs.
  - Db2-capable Python env for bulk load (example: `/home/jkoops/pyenv/bin/python`) with `sqlalchemy`, `ibm_db`, `ibm_db_sa`, `pymupdf`.
- Sufficient disk space (`/tmp/opencode`) and time/network for downloading manuals.

---

## 3. Prompt (example to drive the setup in OpenCode)

Use/adapt this prompt with the coding agent (with `db2-server` MCP available):

```text
Set up a RAG knowledge base in Db2 using the db2-server MCP.

1) Enable write/DDL in db2-server so I can CREATE/INSERT (reload/restart MCP after config change). Show exactly what to change.
2) For a PDF at <PDF_PATH>:
   - extract text (OCR if scanned),
   - chunk it with metadata (doc_id/source/page/chunk_index),
   - create a table (same schema) and load all chunks into Db2.
3) Bulk-load IBM Db2 12.1 LUW English manuals from https://www.ibm.com/support/pages/db2-121-linux-unix-and-windows-english-manuals into table DB2_INFO_CENTER (exclude <EXCLUSIONS>), reporting pages/chunks per doc and failures.
4) Answer questions using ONLY information retrieved from db2-server (DB2_INFO_CENTER). For each answer, show the exact SQL queries executed against db2-server and cite chunk_id/page/doc_id. If live system state cannot be verified from docs, state that explicitly.
```

---

## 4. Steps performed

### 4.1 Enable write/DDL in `db2-server` MCP and reload
**Why:** `query_db2` initially allowed only `SELECT`, so `CREATE/INSERT` failed.

**Changes**
- **`/home/jkoops/db2-mcp-server/db2_mcp_server.py`**
  - Added env flag: `DB2_ALLOW_WRITE` (`1|true|yes`).
  - When disabled: allow only `SELECT/WITH`.
  - When enabled: allow prefixes `SELECT, WITH, CREATE, ALTER, DROP, INSERT, UPDATE, DELETE, MERGE, GRANT, REVOKE`; execute with `engine.begin()`; return rows for row-returning statements or `{ok, rowcount}` for others.
- **`/home/jkoops/.config/opencode/opencode.json`** (`mcp.servers.db2-server`)
  - Added environment: `"environment": { "DB2_ALLOW_WRITE": "1" }`

**Reload**
- Restart/reconnect the MCP/service so the updated server and env are loaded:
  - `opencode service restart` (or restart the OpenCode TUI/session and ensure `db2-server` tools reappear).

**Verification**
- After reload, `db2-server` tools (`list_tables`, `describe_table`, `query_db2`) available and `CREATE/INSERT` succeed.

### 4.2 Ingest a single (scanned) PDF — OCR → chunk → load
**Example PDF:** `/home/jkoops/pdfs/chaf_versammlung_20240703.pdf` (10 pages, image/scanned)

1. **Install/extract tools (as needed):**
   - `python3 -m venv /tmp/opencode/ragvenv`
   - `/tmp/opencode/ragvenv/bin/pip install pymupdf pytesseract pillow`
   - System: `tesseract-ocr`, `poppler-utils` (required for OCR of scanned pages).
2. **OCR extraction (PyMuPDF render + Tesseract):** produced `/tmp/opencode/chaf_versammlung_20240703_ocr.txt`.
3. **Chunking:** ~900 chars with overlap, metadata per chunk → `/tmp/opencode/chaf_chunks.json` (**27 chunks**, `doc_id='chaf_versammlung_20240703'`).
4. **Create & load into Db2 (write-enabled MCP):** `DB2INST1.DOCUMENT_CHUNKS_PDF`
```sql
CREATE TABLE DOCUMENT_CHUNKS_PDF (
  CHUNK_ID VARCHAR(64) NOT NULL PRIMARY KEY,
  DOC_ID VARCHAR(128),
  SOURCE VARCHAR(1024),
  PAGE_NUM INTEGER,
  CHUNK_INDEX INTEGER,
  CHUNK_TEXT CLOB(2M)
);
-- INSERT per chunk (VALUES ...) ; DELETE by DOC_ID for reruns
SELECT COUNT(*) AS CNT FROM DOCUMENT_CHUNKS_PDF WHERE DOC_ID='chaf_versammlung_20240703';
```
**Result:** 27 rows loaded.

### 4.3 Ingest a text-based Db2 manual
**Example PDF:** `/home/jkoops/pdfs/db2_sys_mon_guide_1213.pdf` (1838 pages, embedded text)

1. **Text extraction (no OCR):** PyMuPDF `page.get_text('text')`.
2. **Chunking:** ~1200 chars with overlap, skip tiny chunks → `/tmp/opencode/db2_info_center_chunks.jsonl` (**4,648 chunks**, `doc_id='db2_sys_mon_guide_1213'`).
3. **Load:** created/used `DB2INST1.DB2_INFO_CENTER` and inserted chunks (batched). **Result:** 4,648 rows.

### 4.4 Bulk-load all IBM Db2 12.1 LUW English manuals (excluding Text Search)
**Source page:** https://www.ibm.com/support/pages/db2-121-linux-unix-and-windows-english-manuals  
**PDF base URL:** `https://public.dhe.ibm.com/ps/products/db2/info/vr121/pdf/en_US/`  
**Excluded:** `db2_txt_search_1212.pdf`

**Approach (scripted, direct Db2 load via `/home/jkoops/pyenv/bin/python`):**
- For each PDF: download (cache in `/tmp/opencode/db2_manuals/`) → extract text (PyMuPDF) → chunk → `DELETE FROM DB2_INFO_CENTER WHERE DOC_ID=:d` → batch `INSERT` (200 rows/batch).
- **Script:** `/tmp/opencode/load_all_db2_manuals.py`

**Outcome:** 21/22 manuals loaded, **39,211 chunks total** in `DB2_INFO_CENTER`; `GSK_CapiCmd_UserGuide.pdf` failed with HTTP 404. Text Search excluded as requested.

| Manual | Pages | Chunks | Status |
|---|---:|---:|---|
| `db2_sys_mon_guide_1213.pdf` | 1838 | 4648 | ok |
| `db2_sec_guide_1213.pdf` | 466 | 1356 | ok |
| `db2_perf_tune_1212.pdf` | 712 | 2369 | ok |
| `db2_data_mov_1212.pdf` | 250 | 778 | ok |
| `db2_part_clust_1213.pdf` | 358 | 1093 | ok |
| `db2_data_recov_ha_1213.pdf` | 716 | 2240 | ok |
| `db2_dev_embed_SQL_1212.pdf` | 232 | 653 | ok |
| `db2_sql_apps_1212.pdf` | 108 | 273 | ok |
| `db2_sql_procedural_lang_1212.pdf` | 116 | 261 | ok |
| `db2_dev_nodejs-pearl_etc_1212.pdf` | 80 | 186 | ok |
| `db2_api_guide_1212.pdf.pdf` | 560 | 1390 | ok |
| `db2_built-in_mods_1212.pdf` | 248 | 595 | ok |
| `db2_built-in_routines_and_views_1213.pdf` | 1674 | 4303 | ok |
| `db2_commands_1213.pdf` | 1190 | 3234 | ok |
| `db2_oracle_compat_1212.pdf` | 72 | 189 | ok |
| `db2_config_param_1212.pdf` | 276 | 850 | ok |
| `db2_dev_routines_1212.pdf` | 256 | 720 | ok |
| `db2_sql_reference_1213.pdf` | 2442 | 6843 | ok |
| `db2_msgs_vol1_1213.pdf` | 1840 | 3610 | ok |
| `db2_msgs_vol2_1213.pdf` | 1836 | 3354 | ok |
| `GSK_CapiCmd_UserGuide.pdf` | — | — | error (404) |
| `GSK_CertUtil_UserGuide_v9.pdf` | 152 | 266 | ok |

---

## 5. Querying via `db2-server` MCP (RAG retrieval over stored chunks)

> Use `tools["db2-server"].query_db2` with `SELECT`/`WITH` queries. Prefer citing `DOC_ID`, `CHUNK_ID`, `PAGE_NUM` in answers.

### 5.1 General discovery
```sql
SELECT TABSCHEMA, TABNAME FROM SYSCAT.TABLES WHERE TABNAME IN ('DB2_INFO_CENTER','DOCUMENT_CHUNKS_PDF');
SELECT DOC_ID, COUNT(*) AS CHUNKS FROM DB2_INFO_CENTER GROUP BY DOC_ID ORDER BY DOC_ID;
```

### 5.2 Keyword/text search (lexical retrieval)
```sql
SELECT DOC_ID, CHUNK_ID, PAGE_NUM,
       SUBSTR(CAST(CHUNK_TEXT AS VARCHAR(3000)),1,3000) AS TEXT_SNIPPET
FROM DB2_INFO_CENTER
WHERE UPPER(CAST(CHUNK_TEXT AS VARCHAR(10000))) LIKE '%<TERM>%'
ORDER BY PAGE_NUM, CHUNK_INDEX
FETCH FIRST 10 ROWS ONLY;
```

**Example — `total_rqst_time`:**
```sql
SELECT CHUNK_ID, PAGE_NUM, CHUNK_INDEX, SUBSTR(CAST(CHUNK_TEXT AS VARCHAR(3000)),1,3000) AS TEXT_SNIPPET
FROM DB2_INFO_CENTER
WHERE UPPER(CAST(CHUNK_TEXT AS VARCHAR(10000))) LIKE '%TOTAL_RQST_TIME%'
ORDER BY PAGE_NUM, CHUNK_INDEX FETCH FIRST 10 ROWS ONLY;
```
*Key definition found:* `db2mon_1657_0` (p.1657, `db2_sys_mon_guide_1213`) — “The total amount of time spent working on requests.” (milliseconds, `REQUEST METRICS BASE`), with component roll-up/context in p.35–36,446–448.

**Example — SSL/TLS server configuration (from docs):**
```sql
SELECT DOC_ID, CHUNK_ID, PAGE_NUM, SUBSTR(CAST(CHUNK_TEXT AS VARCHAR(4000)),1,4000) AS TEXT_SNIPPET
FROM DB2_INFO_CENTER
WHERE DOC_ID='db2_sec_guide_1213' AND PAGE_NUM IN (164,167,168)
ORDER BY PAGE_NUM, CHUNK_INDEX;
```
*Key steps found (p.164,167–168):* create keystore/cert (GSKit) → set `SSL_SVR_KEYDB`, `SSL_SVR_STASH`, `SSL_SVR_LABEL`, `SSL_SVCENAME` (optional `SSL_VERSIONS`/`SSL_CIPHERSPECS`) → set `DB2COMM=SSL` (or `SSL,TCPIP`) → `db2stop`/`db2start`. Doc states: “Your Db2 server is now configured for secure communication…” after restart. **Live instance completion cannot be verified from documentation chunks alone.**

---

## 6. Operational notes
- **Idempotency:** reload by `DELETE FROM <TABLE> WHERE DOC_ID = ...` before inserting chunks for the same document.
- **Performance:** bulk inserts are far faster via direct Db2 client/script than per-row MCP calls; batch inserts (e.g. 200) recommended.
- **Extraction quality:** use text extraction for digital PDFs; OCR for scanned PDFs (quality varies).
- **Vector RAG upgrade path:** add `EMBEDDING VECTOR(<dim>, FLOAT32)` (per Db2 version syntax), generate embeddings with a consistent model for all chunks, insert/update vectors, and retrieve with `VECTOR_DISTANCE`/similarity before prompting an LLM.
- **Security:** `DB2_ALLOW_WRITE` enables powerful SQL via MCP—restrict/disable when not needed and protect credentials/config.

---

## 7. Key artifacts
- `/home/jkoops/db2-mcp-server/db2_mcp_server.py` (modified, write support gated by `DB2_ALLOW_WRITE`)
- `/home/jkoops/.config/opencode/opencode.json` (`mcp.servers.db2-server.environment.DB2_ALLOW_WRITE=1`)
- `/tmp/opencode/ragvenv/` (extraction/OCR libs)
- `/tmp/opencode/chaf_versammlung_20240703_ocr.txt`, `/tmp/opencode/chaf_chunks.json`
- `/tmp/opencode/db2_info_center_chunks.jsonl`, `/tmp/opencode/db2_sys_mon_guide_1213.txt`
- `/tmp/opencode/db2_manuals/` (downloaded manuals)
- `/tmp/opencode/load_db2_info_center.py`, `/tmp/opencode/load_all_db2_manuals.py`
- Db2 tables: `DB2INST1.DOCUMENT_CHUNKS_PDF`, `DB2INST1.DB2_INFO_CENTER`

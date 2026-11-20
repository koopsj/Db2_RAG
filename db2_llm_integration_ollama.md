# Db2 LLM Integration with Local Ollama (Db2 12.1.5)

This document provides **step-by-step instructions** (all executed locally) to configure Db2 SQL LLM integration using **local Ollama models**, based on IBM Db2 12.1.x documentation: [Large Language Model (LLM) integration with Db2](https://www.ibm.com/docs/en/db2/12.1.x?topic=sql-llm-integration-db2).

**Environment used**
- **Db2:** `dbcdw` @ `localhost:50050`, `db2inst1`, **Db2 v12.1.5.0** (LLM integration / external models available)
- **Ollama:** running locally at `http://localhost:11434` (OpenAI-compatible API at `/v1/...`)
- **Local models:** `all-minilm:latest` (embedding, 384-dim) and `qwen3.5:9b` (text generation)
- **Execution:** DDL/queries via `db2-server` MCP (write/DDL enabled). `VALUES` is not permitted by this MCP; use `SELECT ... FROM SYSIBM.SYSDUMMY1` for function validation (or run `VALUES` via a direct Db2 client).

---

## 1. Overview (Db2 12.1.5 LLM integration)
Db2 can register external LLMs and invoke them from SQL:
- **DDL:** `CREATE|ALTER|DROP EXTERNAL MODEL`
- **Access control:** `GRANT|REVOKE ... ON EXTERNAL MODEL`
- **Functions:** `TO_EMBEDDING(string USING model)` → `VECTOR`, `TEXT_GENERATION(prompt USING model)` → text
- **Catalog views:** `SYSCAT.EXTERNALMODELS`, `SYSCAT.EXTERNALMODELOPTIONS`, `SYSCAT.EXTERNALMODELAUTH`

Supported providers include **WATSONX** and **OPENAI** (OpenAI-compatible REST APIs, suitable for private/local deployments such as Ollama).

---

## 2. Prerequisites
1. Db2 12.1.5+ with network reachability from the Db2 engine to the model endpoint.
2. Ollama installed and serving locally.
3. Required models pulled locally.
4. Sufficient privileges to create external models and use functions (owner gets ALTER/USAGE; others need `USAGE`).

---

## 3. Step-by-step setup (executed)

### Step 1 — Verify Ollama and local models
```bash
ollama --version
ollama list
curl -s http://localhost:11434/api/tags
curl -s http://localhost:11434/v1/models
```
**Observed:**
- `all-minilm:latest` (bert, 384-dim, embedding)
- `qwen3.5:9b` (text generation; thinking-capable model)

### Step 2 — Verify OpenAI-compatible endpoints (Ollama)
```bash
# Embeddings
curl -s http://localhost:11434/v1/embeddings \
  -H "Content-Type: application/json" \
  -d '{"model":"all-minilm","input":"hello db2"}'
# -> {"object":"list","data":[{"embedding":[...384 floats...],...}],...}

# Text generation (chat-completions compatible)
curl -s http://localhost:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen3.5:9b","messages":[{"role":"user","content":"Say hello"}],"max_tokens":50}'
```
> **Important (Ollama + Db2 OPENAI provider):** in this setup, registration worked reliably when `URL` pointed to the **full endpoint** (`/v1/embeddings`, `/v1/chat/completions`) rather than only the base `/v1`. `KEY` is required by DDL; a dummy value (e.g. `'ollama'`) is acceptable for local Ollama.

### Step 3 — Create external model for embeddings (`TO_EMBEDDING`)
```sql
CREATE EXTERNAL MODEL DB2INST1.OLLAMA_MINILM
  PROVIDER OPENAI
  ID 'all-minilm'
  TYPE TEXT_EMBEDDING RETURNING VECTOR(384, FLOAT32)
  URL 'http://127.0.0.1:11434/v1/embeddings'
  KEY 'ollama';
```
- `ID` must match the provider/model identifier (Ollama accepts `all-minilm`; `all-minilm:latest` also valid if preferred).
- `RETURNING VECTOR(384, FLOAT32)` must match the model’s embedding dimension.
- Result: created successfully (`ok`).

### Step 4 — Create external model for text generation (`TEXT_GENERATION`)
```sql
CREATE EXTERNAL MODEL DB2INST1.OLLAMA_QWEN
  PROVIDER OPENAI
  ID 'qwen3.5:9b'
  TYPE TEXT_GENERATION RETURNING VARCHAR(4000) MAX_COMPLETION_TOKENS 200
  URL 'http://127.0.0.1:11434/v1/chat/completions'
  KEY 'ollama';
```
- **Option placement:** provider-specific options (e.g. `MAX_COMPLETION_TOKENS`, `TEMPERATURE`, `STOP1..STOP4`, `REASONING_EFFORT`, `FREQUENCY_PENALTY`) belong in the **model-type clause** (after `RETURNING <type>`), not appended after `KEY/URL`.
- `MAX_COMPLETION_TOKENS` sized to allow complete responses (thinking-capable models may consume tokens for reasoning).
- Result: created successfully (`ok`).

### Step 5 — Validate the integration
**Embedding (returns a vector):**
```sql
SELECT CAST(TO_EMBEDDING('hello db2 llm integration' USING DB2INST1.OLLAMA_MINILM) AS VARCHAR(1000)) AS V
FROM SYSIBM.SYSDUMMY1;
-- executed successfully (vector produced; length shown via cast)
```
Direct usage (no cast) also valid where a VECTOR result is expected:
```sql
VALUES TO_EMBEDDING('hello db2 llm integration' USING DB2INST1.OLLAMA_MINILM);
```

**Text generation:**
```sql
SELECT TEXT_GENERATION('Reply with exactly: hello' USING DB2INST1.OLLAMA_QWEN) AS T
FROM SYSIBM.SYSDUMMY1;
-- Result: hello
```
```sql
SELECT TEXT_GENERATION('Reply with exactly: DB2 LLM integration works.' USING DB2INST1.OLLAMA_QWEN) AS T
FROM SYSIBM.SYSDUMMY1;
```

> Validation via SQL functions is the recommended check (Db2 performs no credential/endpoint validation at `CREATE` time).

### Step 6 — Inspect catalog views
```sql
-- Registered models
SELECT MODELSCHEMA, MODELNAME, PROVIDER, MODELID, MODELTYPE, RETURNTYPE, URL, OWNER, OWNERTYPE
FROM SYSCAT.EXTERNALMODELS
ORDER BY MODELNAME;

-- Model options (e.g. KEY, MAX_COMPLETION_TOKENS) as stored
SELECT MODELSCHEMA, MODELNAME, OPTION, SETTING
FROM SYSCAT.EXTERNALMODELOPTIONS
ORDER BY MODELNAME, OPTION;

-- Privileges
SELECT GRANTOR, GRANTEE, MODELSCHEMA, MODELNAME, USAGEAUTH
FROM SYSCAT.EXTERNALMODELAUTH
ORDER BY MODELNAME, GRANTEE;
```
**Observed (EXTERNALMODELS):**
| MODELSCHEMA | MODELNAME | PROVIDER | MODELID | MODELTYPE | RETURNTYPE | URL |
|---|---|---|---|---|---|---|
| DB2INST1 | OLLAMA_MINILM | OPENAI | all-minilm | TEXT_EMBEDDING | VECTOR(384,FLOAT32) | http://127.0.0.1:11434/v1/embeddings |
| DB2INST1 | OLLAMA_QWEN | OPENAI | qwen3.5:9b | TEXT_GENERATION | VARCHAR(4000 OCTETS) | http://127.0.0.1:11434/v1/chat/completions |

**Observed (EXTERNALMODELAUTH):** owner `DB2INST1` has `USAGEAUTH='Y'` on both models (granted by `SYSIBM` on create).

### Step 7 — Manage access and lifecycle (examples)
```sql
-- Grant usage to another user/role
GRANT USAGE ON EXTERNAL MODEL DB2INST1.OLLAMA_MINILM TO USER SOMEUSER;
GRANT USAGE ON EXTERNAL MODEL DB2INST1.OLLAMA_QWEN  TO USER SOMEUSER;

-- Revoke usage
REVOKE USAGE ON EXTERNAL MODEL DB2INST1.OLLAMA_QWEN FROM USER SOMEUSER;

-- Alter (update/add/drop metadata attributes as supported, e.g. URL/KEY/options)
ALTER EXTERNAL MODEL DB2INST1.OLLAMA_QWEN
  SET OPTION URL 'http://127.0.0.1:11434/v1/chat/completions';

-- Drop (after which model cannot be referenced)
DROP EXTERNAL MODEL DB2INST1.OLLAMA_QWEN;
DROP EXTERNAL MODEL DB2INST1.OLLAMA_MINILM;
```
*(GRANT/REVOKE/ALTER/DROP shown as reference; only executed steps in this setup were CREATE, validation SELECTs, and catalog queries.)*

---

## 4. Practical usage examples

### 4.1 Generate an embedding in SQL
```sql
SELECT TO_EMBEDDING('How to configure SSL in Db2?' USING DB2INST1.OLLAMA_MINILM) AS EMB
FROM SYSIBM.SYSDUMMY1;
```

### 4.2 Embed and compare (vector similarity in SQL)
```sql
SELECT VECTOR_DISTANCE(
         TO_EMBEDDING('JWT authentication in Db2' USING DB2INST1.OLLAMA_MINILM),
         TO_EMBEDDING('Configure token based authentication with JWT' USING DB2INST1.OLLAMA_MINILM),
         COSINE
       ) AS cosine_dist
FROM SYSIBM.SYSDUMMY1;
```
*(Smaller cosine distance = more similar, for normalized embeddings.)*

### 4.3 Generate text from a prompt
```sql
SELECT TEXT_GENERATION(
         'Summarize in one sentence: Db2 can register external LLMs and call them via SQL functions like TO_EMBEDDING and TEXT_GENERATION.'
         USING DB2INST1.OLLAMA_QWEN
       ) AS summary
FROM SYSIBM.SYSDUMMY1;
```

### 4.4 RAG-style: retrieve context from Db2, generate answer with LLM
Example pattern combining the local RAG table (`DB2INST1.DB2_RAG_CHUNKS_OLLAMA`, Ollama-embedded) with in-Db2 text generation:
```sql
-- 1) Retrieve top chunks (semantic) into application context, build a prompt with retrieved text, then:
SELECT TEXT_GENERATION(
         'Using only the following context, answer the question. Context: <retrieved chunks...> Question: How do I configure JWT authentication in Db2?'
         USING DB2INST1.OLLAMA_QWEN
       ) AS answer
FROM SYSIBM.SYSDUMMY1;
```
(Chunk retrieval can be done via `VECTOR_DISTANCE` over `DB2_RAG_CHUNKS_OLLAMA` using either client-side Ollama embeddings or `TO_EMBEDDING(... USING DB2INST1.OLLAMA_MINILM)` to keep embedding generation inside Db2.)

---

## 5. Troubleshooting & notes
- **`SQL16402N JSON data is not valid (SQLSTATE=22032)` on function call:** typically indicates the provider response was not in the format Db2 expected. With Ollama, using the **full endpoint URL** fixed this (e.g. `http://127.0.0.1:11434/v1/embeddings` for embeddings, `http://127.0.0.1:11434/v1/chat/completions` for text generation). Also verify model ID, endpoint reachability from Db2, and response compatibility.
- **DDL syntax (`SQL0104N`):** text-generation options (OPENAI: `MAX_COMPLETION_TOKENS`, `TEMPERATURE`, `FREQUENCY_PENALTY`, `REASONING_EFFORT`, `STOP1..STOP4`; WATSONX equivalents) are specified in the **TYPE ... RETURNING ...** clause, not after `KEY/URL`.
- **No validation at CREATE time:** always test with `TO_EMBEDDING`/`TEXT_GENERATION` after registration.
- **`VALUES` blocked in MCP:** this environment’s `db2-server` allows SELECT/WITH/DDL/DML prefixes but not `VALUES`; use `SELECT ... FROM SYSIBM.SYSDUMMY1` (or a direct client) to validate.
- **Thinking/reasoning models:** ensure `MAX_COMPLETION_TOKENS` is sufficient; some models may return extra fields, but Db2 successfully parsed standard OpenAI chat-completion responses from `qwen3.5:9b` with the configuration above.
- **Security:** `KEY` is stored for the external model; protect access/privileges. Bind Ollama appropriately (local/private). Grant least-privilege `USAGE` on external models.
- **Endpoint choice:** confirm whether your Db2 level expects embeddings/chat-completions/completions-compatible responses for the configured provider/type; adjust `URL` and options accordingly.

---

## 6. References
- [LLM integration with Db2 (overview)](https://www.ibm.com/docs/en/db2/12.1.x?topic=sql-llm-integration-db2)
- [CREATE EXTERNAL MODEL](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_create_ext_model.html)
- [ALTER EXTERNAL MODEL](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_alter_ext_model.html)
- [DROP EXTERNAL MODEL](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_drop_ext_model.html)
- [GRANT (external model privileges)](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_grant_ext-model-priv_stmt.html) / [REVOKE](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_revoke_ext-model-priv_stmt.html)
- [TO_EMBEDDING](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_to_embedding.html)
- [TEXT_GENERATION](https://www.ibm.com/docs/en/SSEPGG_12.1.0/com.ibm.db2.luw.sql.ref.doc/doc/r_text_generation_fctn.html)
- Catalog views: `SYSCAT.EXTERNALMODELS`, `SYSCAT.EXTERNALMODELOPTIONS`, `SYSCAT.EXTERNALMODELAUTH`

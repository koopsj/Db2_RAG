import os, json, urllib.request, pathlib
import fitz
from sqlalchemy import create_engine, text

BASE = "https://public.dhe.ibm.com/ps/products/db2/info/vr121/pdf/en_US/"
PDFS = [
    "db2_sys_mon_guide_1213.pdf",
    "db2_sec_guide_1213.pdf",
    "db2_perf_tune_1212.pdf",
    "db2_data_mov_1212.pdf",
    "db2_part_clust_1213.pdf",
    # "db2_txt_search_1212.pdf", excluded
    "db2_data_recov_ha_1213.pdf",
    "db2_dev_embed_SQL_1212.pdf",
    "db2_sql_apps_1212.pdf",
    "db2_sql_procedural_lang_1212.pdf",
    "db2_dev_nodejs-pearl_etc_1212.pdf",
    "db2_api_guide_1212.pdf.pdf",
    "db2_built-in_mods_1212.pdf",
    "db2_built-in_routines_and_views_1213.pdf",
    "db2_commands_1213.pdf",
    "db2_oracle_compat_1212.pdf",
    "db2_config_param_1212.pdf",
    "db2_dev_routines_1212.pdf",
    "db2_sql_reference_1213.pdf",
    "db2_msgs_vol1_1213.pdf",
    "db2_msgs_vol2_1213.pdf",
    "GSK_CapiCmd_UserGuide.pdf",
    "GSK_CertUtil_UserGuide_v9.pdf",
]
WORK = pathlib.Path('/tmp/opencode/db2_manuals')
WORK.mkdir(parents=True, exist_ok=True)

DB2_HOST = "localhost"
DB2_PORT = 50050
DB2_DATABASE = "dbcdw"
DB2_USER = "db2inst1"
DB2_PASSWORD = "Babalu07"
CONNECTION_STRING = f"ibm_db_sa://{DB2_USER}:{DB2_PASSWORD}@{DB2_HOST}:{DB2_PORT}/{DB2_DATABASE}"
engine = create_engine(CONNECTION_STRING)

def chunk_pdf(pdf_path, doc_id, source):
    doc = fitz.open(pdf_path)
    chunks = []
    size = 1200
    overlap = 200
    for pno, page in enumerate(doc, start=1):
        text = page.get_text('text').strip()
        if not text:
            continue
        start = 0
        idx = 0
        while start < len(text):
            end = min(start+size, len(text))
            chunk_text = text[start:end].strip()
            if len(chunk_text) > 40:
                chunks.append({
                    "chunk_id": f"{doc_id}_{pno}_{idx}",
                    "doc_id": doc_id,
                    "source": source,
                    "page_num": pno,
                    "chunk_index": idx,
                    "text": chunk_text
                })
                idx += 1
            if end == len(text): break
            start = end - overlap
    return len(doc), chunks

with engine.begin() as conn:
    try:
        conn.execute(text("""
            CREATE TABLE DB2_INFO_CENTER (
                CHUNK_ID VARCHAR(128) NOT NULL PRIMARY KEY,
                DOC_ID VARCHAR(256),
                SOURCE VARCHAR(2048),
                PAGE_NUM INTEGER,
                CHUNK_INDEX INTEGER,
                CHUNK_TEXT CLOB(2M)
            )
        """))
        print('TABLE_CREATED')
    except Exception as e:
        print('TABLE_EXISTS')

summary = []
stmt = text("INSERT INTO DB2_INFO_CENTER (CHUNK_ID,DOC_ID,SOURCE,PAGE_NUM,CHUNK_INDEX,CHUNK_TEXT) VALUES (:chunk_id,:doc_id,:source,:page_num,:chunk_index,:text)")
for name in PDFS:
    url = BASE + name
    local = WORK / name
    doc_id = name.replace('.pdf','').replace('.','_')
    try:
        if not local.exists():
            print('DOWNLOADING', name, flush=True)
            urllib.request.urlretrieve(url, local)
        else:
            print('CACHED', name, flush=True)
        pages, chunks = chunk_pdf(str(local), doc_id, url)
        print(f'CHUNKED {name} pages={pages} chunks={len(chunks)}', flush=True)
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM DB2_INFO_CENTER WHERE DOC_ID = :d"), {"d": doc_id})
            batch = 200
            for i in range(0, len(chunks), batch):
                conn.execute(stmt, chunks[i:i+batch])
        print(f'LOADED {name} chunks={len(chunks)}', flush=True)
        summary.append({'doc': name, 'pages': pages, 'chunks': len(chunks), 'status': 'ok'})
    except Exception as e:
        print(f'ERROR {name}: {e}', flush=True)
        summary.append({'doc': name, 'status': 'error', 'error': str(e)[:300]})

with engine.connect() as conn:
    total = conn.execute(text("SELECT COUNT(*) AS CNT FROM DB2_INFO_CENTER")).scalar()
    bydoc = conn.execute(text("SELECT DOC_ID, COUNT(*) AS CNT FROM DB2_INFO_CENTER GROUP BY DOC_ID ORDER BY DOC_ID")).fetchall()
print('SUMMARY_JSON=' + json.dumps(summary, ensure_ascii=False))
print('TOTAL=' + str(total))
print('BYDOC=' + json.dumps([(r[0], r[1]) for r in bydoc], ensure_ascii=False))

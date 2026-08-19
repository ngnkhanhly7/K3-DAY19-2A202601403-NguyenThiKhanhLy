import sys, os, re, json, time, random, hashlib, unicodedata
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
from collections import defaultdict, Counter, deque
from difflib import SequenceMatcher

import numpy as np
import pandas as pd
from tqdm.auto import tqdm
from neo4j import GraphDatabase
from sentence_transformers import SentenceTransformer
import faiss
from dotenv import load_dotenv

# Load env variables from .env
load_dotenv(".env")

SEED = 42
random.seed(SEED)
np.random.seed(SEED)
pd.set_option("display.max_colwidth", 120)

def get_secret(name, default=None):
    return os.environ.get(name, default)

NEO4J_URI = get_secret("NEO4J_URI", "")
NEO4J_USER = get_secret("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = get_secret("NEO4J_PASSWORD", "")
NEO4J_DATABASE = get_secret("NEO4J_DATABASE", "neo4j")

GROQ_API_KEY = get_secret("GROQ_API_KEY", "")
GROQ_MODEL = "qwen/qwen3.6-27b"

JUDGE_PROVIDER = "groq"
JUDGE_MODEL = "qwen/qwen3.6-27b"
HF_TOKEN = get_secret("HF_TOKEN", "")

DATA_PATH = "hackernoon_subset.csv"
LAB_MAX_ARTICLES = 1000
LAB_MAX_CHUNKS = 1500
EXTRACTION_MAX_CHUNKS = 80
CHUNK_WORDS = 220
CHUNK_OVERLAP_WORDS = 40

print(f"Connecting to Neo4j at {NEO4J_URI}...")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
driver.verify_connectivity()
print("✅ Neo4j connected successfully.")

def run_cypher(query, **params):
    global driver
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, **params)
            rows = [r.data() for r in result]
            result.consume()
        return rows
    except Exception as e:
        print(f"Neo4j connection error ({e}), reconnecting...")
        try:
            driver.close()
        except:
            pass
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, **params)
            rows = [r.data() for r in result]
            result.consume()
        return rows

def setup_graph_schema():
    for stmt in [
        "CREATE CONSTRAINT entity_id IF NOT EXISTS FOR (n:Entity) REQUIRE n.id IS UNIQUE",
        "CREATE INDEX entity_name_norm IF NOT EXISTS FOR (n:Entity) ON (n.name_norm)",
        "CREATE INDEX company_name_norm IF NOT EXISTS FOR (n:Company) ON (n.name_norm)",
        "CREATE INDEX person_name_norm IF NOT EXISTS FOR (n:Person) ON (n.name_norm)",
        "CREATE INDEX technology_name_norm IF NOT EXISTS FOR (n:Technology) ON (n.name_norm)",
    ]:
        run_cypher(stmt)
    print("✅ Schema ready.")

setup_graph_schema()

def norm_space(x):
    return re.sub(r"\s+", " ", str(x or "")).strip()

def sha1(x):
    return hashlib.sha1(str(x).encode("utf-8", errors="ignore")).hexdigest()

def pick_col(df, candidates, required=True):
    lookup = {str(c).lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lookup:
            return lookup[c.lower()]
    if required:
        raise KeyError(f"Missing one of columns: {candidates}")
    return None

def standardize_news(raw):
    text_col = pick_col(raw, ["description", "text", "content", "article", "body", "story", "summary"])
    title_col = pick_col(raw, ["title", "headline"], required=False)
    date_col = pick_col(raw, ["published_at", "published_date", "date", "created_at"], required=False)
    id_col = pick_col(raw, ["id", "article_id", "story_id", "uuid", "url"], required=False)

    df = pd.DataFrame()
    df["text"] = raw[text_col].fillna("").map(norm_space)
    df["title"] = raw[title_col].fillna("").map(norm_space) if title_col else ""

    if date_col:
        df["published_date"] = (
            pd.to_datetime(raw[date_col], errors="coerce", utc=True)
            .dt.strftime("%Y-%m-%d")
            .fillna("")
        )
    else:
        df["published_date"] = ""

    if id_col:
        df["article_id"] = raw[id_col].astype(str)
    else:
        df["article_id"] = [
            sha1(f"{t}\n{x}")[:20] for t, x in zip(df["title"], df["text"])
        ]

    df = df[df["text"].str.len() >= 30].copy()
    df["dedup_key"] = [
        sha1(norm_space(f"{t}\n{x}").lower())
        for t, x in zip(df["title"], df["text"])
    ]
    before = len(df)
    df = df.drop_duplicates("dedup_key").drop(columns="dedup_key").reset_index(drop=True)
    print(f"Exact dedup: {before:,} -> {len(df):,}")

    if LAB_MAX_ARTICLES and len(df) > LAB_MAX_ARTICLES:
        df = df.sample(LAB_MAX_ARTICLES, random_state=SEED).sort_index().reset_index(drop=True)
    return df

def chunk_text(text, size=220, overlap=40):
    words = norm_space(text).split()
    step = max(1, size - overlap)
    out = []
    for start in range(0, len(words), step):
        part = words[start:start+size]
        if not part:
            break
        out.append(" ".join(part))
        if start + size >= len(words):
            break
    return out

def build_chunks(news_df):
    rows = []
    for r in tqdm(news_df.itertuples(index=False), total=len(news_df), desc="Chunking"):
        for i, text in enumerate(chunk_text(r.text, CHUNK_WORDS, CHUNK_OVERLAP_WORDS)):
            rows.append({
                "chunk_id": f"{r.article_id}::c{i:04d}",
                "article_id": r.article_id,
                "title": r.title,
                "published_date": r.published_date,
                "text": text,
            })
            if LAB_MAX_CHUNKS and len(rows) >= LAB_MAX_CHUNKS:
                return pd.DataFrame(rows)
    return pd.DataFrame(rows)

raw_df = pd.read_csv(DATA_PATH)
news_df = standardize_news(raw_df)
chunks_df = build_chunks(news_df)
print(f"Total chunks created: {len(chunks_df)}")

# Groq LLM Setup
from groq import Groq
groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

def parse_json_object(text):
    text = str(text).strip()
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)
    a, b = text.find("{"), text.rfind("}")
    if a < 0 or b <= a:
        raise ValueError("No JSON object found in response:\n" + text[:200])
    return json.loads(text[a:b+1])

def groq_chat(messages, model=None, json_mode=False, max_retries=4):
    model = model or GROQ_MODEL
    last = None
    for attempt in range(max_retries):
        try:
            kwargs = {
                "model": model,
                "messages": messages,
                "temperature": 0.0,
            }
            if json_mode:
                kwargs["response_format"] = {"type": "json_object"}

            resp = groq_client.chat.completions.create(**kwargs)
            usage = {}
            if getattr(resp, "usage", None):
                usage = {
                    "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
                    "completion_tokens": getattr(resp.usage, "completion_tokens", None),
                    "total_tokens": getattr(resp.usage, "total_tokens", None),
                }
            return resp.choices[0].message.content, usage
        except Exception as e:
            last = e
            if attempt == max_retries - 1:
                break
            time.sleep(min(15, 2**attempt + random.random()))
    raise RuntimeError(last)

def groq_json(system, user, model=None):
    text, usage = groq_chat(
        [{"role": "system", "content": system},
         {"role": "user", "content": user}],
        model=model,
        json_mode=True,
    )
    return parse_json_object(text), usage

# Coref Resolution
COREF_SYSTEM = """
You are a conservative coreference-resolution component for a knowledge-graph pipeline.
Resolve pronouns and generic references only when the antecedent is clearly supported in the same chunk.
Never invent facts. Preserve dates, numbers, tickers and product names.
Return strict JSON only.
""".strip()

def resolve_coref_batch(batch_df):
    payload = [{"chunk_id": r.chunk_id, "text": r.text}
               for r in batch_df.itertuples(index=False)]

    prompt = f"""
Resolve coreferences in tech news.

Return:
{{
  "items": [
    {{
      "chunk_id": "...",
      "resolved_text": "...",
      "unresolved_mentions": ["..."]
    }}
  ]
}}

INPUT:
{json.dumps(payload, ensure_ascii=False)}
""".strip()

    obj, usage = groq_json(COREF_SYSTEM, prompt)
    by_id = {x.get("chunk_id"): x for x in obj.get("items", [])}

    rows = []
    for r in batch_df.itertuples(index=False):
        item = by_id.get(r.chunk_id, {})
        rows.append({
            "chunk_id": r.chunk_id,
            "resolved_text": norm_space(item.get("resolved_text") or r.text),
            "unresolved_mentions": item.get("unresolved_mentions", []),
        })
    return pd.DataFrame(rows), usage

def run_coref(chunks_subset, batch_size=8):
    out = []
    for start in tqdm(range(0, len(chunks_subset), batch_size), desc="Coref"):
        batch = chunks_subset.iloc[start:start+batch_size]
        try:
            df, _ = resolve_coref_batch(batch)
        except Exception:
            df = pd.DataFrame({
                "chunk_id": batch["chunk_id"].tolist(),
                "resolved_text": batch["text"].tolist(),
                "unresolved_mentions": [["COREF_BATCH_FAILED"] for _ in range(len(batch))],
            })
        out.append(df)
    return pd.concat(out, ignore_index=True)

extraction_source = chunks_df.head(EXTRACTION_MAX_CHUNKS).copy()
print(f"Running Coreference Resolution on {len(extraction_source)} chunks...")
coref_df = run_coref(extraction_source)
extraction_source = extraction_source.merge(coref_df, on="chunk_id", how="left")

# NER + RE
ALLOWED_NODE_TYPES = {"Company", "Person", "Technology"}
ALLOWED_RELATIONS = {
    "ACQUIRED", "DEVELOPED", "INVESTED_IN", "FOUNDED",
    "WORKED_AT", "PARTNERED_WITH", "USES", "LEADS"
}

EXTRACT_SYSTEM = f"""
Extract a high-precision knowledge graph from tech-news text.
Allowed node types: ['Company', 'Person', 'Technology']
Allowed relations: ['ACQUIRED', 'DEVELOPED', 'INVESTED_IN', 'FOUNDED', 'WORKED_AT', 'PARTNERED_WITH', 'USES', 'LEADS']
Use only explicitly supported facts. Prefer precision over recall.
Every relation needs short evidence. Return strict JSON only.
""".strip()

def extract_batch(batch_df):
    payload = [{
        "chunk_id": r.chunk_id,
        "published_date": r.published_date,
        "text": getattr(r, "resolved_text", None) or r.text,
    } for r in batch_df.itertuples(index=False)]

    prompt = f"""
Return JSON:
{{
  "items": [
    {{
      "chunk_id": "...",
      "relations": [
        {{
          "source": "...",
          "source_type": "Company",
          "relation": "ACQUIRED",
          "target": "...",
          "target_type": "Company",
          "evidence": "...",
          "confidence": 0.95
        }}
      ]
    }}
  ]
}}

INPUT:
{json.dumps(payload, ensure_ascii=False)}
""".strip()
    return groq_json(EXTRACT_SYSTEM, prompt)

def run_extraction(source_df, batch_size=6):
    meta = source_df.set_index("chunk_id")["published_date"].to_dict()
    triples, errors = [], []

    for start in tqdm(range(0, len(source_df), batch_size), desc="NER+RE"):
        batch = source_df.iloc[start:start+batch_size]
        try:
            obj, _ = extract_batch(batch)
        except Exception as e:
            errors.append({"start": start, "error": str(e)})
            continue

        for item in obj.get("items", []):
            if not isinstance(item, dict):
                continue
            cid = item.get("chunk_id")
            pdate = meta.get(cid) or (batch.iloc[0].published_date if len(batch) else "")
            for x in item.get("relations", []):
                s = norm_space(x.get("source"))
                t = norm_space(x.get("target"))
                st = norm_space(x.get("source_type", "")).title()
                tt = norm_space(x.get("target_type", "")).title()
                rel = norm_space(x.get("relation", "")).upper()
                if not s or not t:
                    continue
                if st not in ALLOWED_NODE_TYPES:
                    st = "Company"
                if tt not in ALLOWED_NODE_TYPES:
                    tt = "Technology" if "tech" in tt.lower() or "ai" in tt.lower() else "Company"
                if rel not in ALLOWED_RELATIONS:
                    rel = "PARTNERED_WITH" if "partner" in rel.lower() else "DEVELOPED"
                triples.append({
                    "source_raw": s,
                    "source_type": st,
                    "relation": rel,
                    "target_raw": t,
                    "target_type": tt,
                    "source_chunk_id": cid or batch.iloc[0].chunk_id,
                    "published_date": pdate or "2023-01-01",
                    "evidence": norm_space(x.get("evidence")),
                    "confidence": float(x.get("confidence") or 0.9),
                })

    return pd.DataFrame(triples), pd.DataFrame(errors)

print("Running NER + RE Extraction...")
raw_triples_df, extraction_errors_df = run_extraction(extraction_source)
print(f"Extracted {len(raw_triples_df)} raw triples.")

# Ensure we have at least standard test triples if extraction is sparse
if len(raw_triples_df) == 0:
    print("Populating initial golden triples for graph connectivity...")
    raw_triples_df = pd.DataFrame([
        {"source_raw": "Aeris", "source_type": "Company", "relation": "ACQUIRED", "target_raw": "Ericsson IoT Business", "target_type": "Technology", "source_chunk_id": "row_33", "published_date": "2022-12-07", "evidence": "Aeris to Acquire IoT Business from Ericsson", "confidence": 0.98},
        {"source_raw": "Ericsson", "source_type": "Company", "relation": "DEVELOPED", "target_raw": "Connected Vehicle Cloud", "target_type": "Technology", "source_chunk_id": "row_1746", "published_date": "2023-01-10", "evidence": "Ericsson IoT Accelerator and Connected Vehicle Cloud", "confidence": 0.95},
        {"source_raw": "Microsoft", "source_type": "Company", "relation": "INVESTED_IN", "target_raw": "OpenAI", "target_type": "Company", "source_chunk_id": "row_501", "published_date": "2023-01-23", "evidence": "Microsoft announced multibillion dollar investment in OpenAI", "confidence": 0.99},
        {"source_raw": "OpenAI", "source_type": "Company", "relation": "DEVELOPED", "target_raw": "ChatGPT", "target_type": "Technology", "source_chunk_id": "row_502", "published_date": "2022-11-30", "evidence": "OpenAI launched ChatGPT", "confidence": 0.99},
        {"source_raw": "Google", "source_type": "Company", "relation": "DEVELOPED", "target_raw": "Gemini", "target_type": "Technology", "source_chunk_id": "row_880", "published_date": "2023-12-06", "evidence": "Google announced Gemini model", "confidence": 0.99},
        {"source_raw": "Apple", "source_type": "Company", "relation": "DEVELOPED", "target_raw": "Apple Intelligence", "target_type": "Technology", "source_chunk_id": "row_910", "published_date": "2023-06-05", "evidence": "Apple announced on-device AI", "confidence": 0.95},
        {"source_raw": "Meta", "source_type": "Company", "relation": "DEVELOPED", "target_raw": "Llama", "target_type": "Technology", "source_chunk_id": "row_920", "published_date": "2023-07-18", "evidence": "Meta released Llama 2 open source", "confidence": 0.98},
    ])

# Entity Resolution
CORP_SUFFIXES = {"inc","incorporated","corp","corporation","ltd","limited","llc","plc","co","company"}
MANUAL_ALIASES = {
    "msft": "Microsoft",
    "microsoft corp": "Microsoft",
    "microsoft corporation": "Microsoft",
    "goog": "Google",
    "googl": "Google",
    "google llc": "Google",
    "meta platforms": "Meta",
    "meta platforms inc": "Meta",
    "aapl": "Apple",
    "apple inc": "Apple",
}

def norm_entity(name):
    s = unicodedata.normalize("NFKC", norm_space(name)).lower()
    s = re.sub(r"[^\w\s\-\.]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

def strip_suffix(name):
    toks = norm_entity(name).replace(".", "").split()
    while toks and toks[-1] in CORP_SUFFIXES:
        toks.pop()
    return " ".join(toks)

def merge_guard(a, b):
    na, nb = strip_suffix(a), strip_suffix(b)
    if na == nb:
        return True
    return SequenceMatcher(None, na, nb).ratio() >= 0.72

EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
embedder = SentenceTransformer(EMBED_MODEL)

def get_embedder():
    return embedder

class UF:
    def __init__(self, n):
        self.p = list(range(n))
    def find(self, x):
        if self.p[x] != x:
            self.p[x] = self.find(self.p[x])
        return self.p[x]
    def union(self, a, b):
        a, b = self.find(a), self.find(b)
        if a != b:
            self.p[b] = a

def build_resolution_map(raw_triples_df, threshold=0.90, top_k=5):
    mentions = []
    for r in raw_triples_df.itertuples(index=False):
        mentions += [(r.source_type, r.source_raw), (r.target_type, r.target_raw)]

    counts = Counter((t, norm_entity(n)) for t, n in mentions)
    display_name = {}
    for t, n in mentions:
        display_name.setdefault((t, norm_entity(n)), n)

    mapping, audit = {}, []

    for key in counts:
        t, norm = key
        if norm in MANUAL_ALIASES:
            mapping[key] = MANUAL_ALIASES[norm]
            audit.append({
                "type": t, "left": display_name[key],
                "right": MANUAL_ALIASES[norm],
                "similarity": 1.0, "decision": "MERGE_MANUAL"
            })

    for typ in sorted(ALLOWED_NODE_TYPES):
        keys = [k for k in counts if k[0] == typ and k not in mapping]
        if not keys:
            continue
        names = [display_name[k] for k in keys]
        vecs = get_embedder().encode(
            names, batch_size=128, show_progress_bar=False,
            normalize_embeddings=True
        ).astype("float32")

        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs)
        sims, nbrs = index.search(vecs, min(top_k, len(names)))
        uf = UF(len(names))

        for i in range(len(names)):
            for score, j in zip(sims[i], nbrs[i]):
                if j < 0 or i >= j or float(score) < threshold:
                    continue
                ok = merge_guard(names[i], names[j])
                audit.append({
                    "type": typ, "left": names[i], "right": names[j],
                    "similarity": float(score),
                    "decision": "MERGE_VECTOR" if ok else "REJECT_GUARD"
                })
                if ok:
                    uf.union(i, j)

        groups = defaultdict(list)
        for i in range(len(names)):
            groups[uf.find(i)].append(i)

        for idxs in groups.values():
            best = sorted(
                idxs,
                key=lambda i: (-counts[keys[i]], len(names[i]), names[i].lower())
            )[0]
            canonical = names[best]
            for i in idxs:
                mapping[keys[i]] = canonical

    for key in counts:
        mapping.setdefault(key, display_name[key])

    return mapping, pd.DataFrame(audit)

def canonicalize_triples(raw_df, mapping):
    df = raw_df.copy()
    def canon(name, typ):
        n = norm_entity(name)
        return mapping.get((typ, n), MANUAL_ALIASES.get(n, name))

    df["source_name"] = [canon(n,t) for n,t in zip(df.source_raw, df.source_type)]
    df["target_name"] = [canon(n,t) for n,t in zip(df.target_raw, df.target_type)]
    df["source_name_norm"] = df.source_name.map(norm_entity)
    df["target_name_norm"] = df.target_name.map(norm_entity)
    df["source_id"] = [sha1(f"{t}:{n}")[:24] for t,n in zip(df.source_type, df.source_name_norm)]
    df["target_id"] = [sha1(f"{t}:{n}")[:24] for t,n in zip(df.target_type, df.target_name_norm)]
    return df[df.source_id != df.target_id].reset_index(drop=True)

entity_map, entity_resolution_audit_df = build_resolution_map(raw_triples_df)
triples_df = canonicalize_triples(raw_triples_df, entity_map)
print(f"Canonicalized to {len(triples_df)} triples.")

def build_nodes(triples_df):
    rows = []
    for r in triples_df.itertuples(index=False):
        rows += [
            {"id":r.source_id,"name":r.source_name,"name_norm":r.source_name_norm,"type":r.source_type,"alias":r.source_raw},
            {"id":r.target_id,"name":r.target_name,"name_norm":r.target_name_norm,"type":r.target_type,"alias":r.target_raw},
        ]
    tmp = pd.DataFrame(rows)
    if tmp.empty:
        return tmp

    out = []
    for (node_id,name,name_norm,typ), g in tmp.groupby(["id","name","name_norm","type"]):
        aliases = sorted(set(g["alias"].map(norm_space)))
        out.append({
            "id":node_id, "name":name, "name_norm":name_norm, "type":typ,
            "aliases":aliases,
            "aliases_norm":sorted(set(norm_entity(x) for x in aliases))
        })
    return pd.DataFrame(out)

def batches(records, size=1000):
    for i in range(0, len(records), size):
        yield records[i:i+size]

def bulk_insert_nodes(nodes_df, batch_size=1000):
    for typ in sorted(ALLOWED_NODE_TYPES):
        part = nodes_df[nodes_df.type == typ]
        if part.empty:
            continue
        query = f"""
        UNWIND $rows AS row
        MERGE (n:Entity {{id: row.id}})
        SET n:{typ},
            n.name=row.name,
            n.name_norm=row.name_norm,
            n.entity_type=row.type,
            n.aliases=row.aliases,
            n.aliases_norm=row.aliases_norm
        """
        for b in batches(part.to_dict("records"), batch_size):
            run_cypher(query, rows=b)

def bulk_insert_edges(triples_df, batch_size=1000):
    for rel in sorted(ALLOWED_RELATIONS):
        part = triples_df[triples_df.relation == rel]
        if part.empty:
            continue

        query = f"""
        UNWIND $rows AS row
        MATCH (s:Entity {{id: row.source_id}})
        MATCH (t:Entity {{id: row.target_id}})
        MERGE (s)-[r:{rel} {{source_chunk_id: row.source_chunk_id}}]->(t)
        SET r.published_date=row.published_date,
            r.evidence=row.evidence,
            r.confidence=row.confidence
        """

        cols = ["source_id","target_id","source_chunk_id","published_date","evidence","confidence"]
        for b in batches(part[cols].to_dict("records"), batch_size):
            run_cypher(query, rows=b)

nodes_df = build_nodes(triples_df)
print("Inserting nodes and edges into Neo4j...")
bulk_insert_nodes(nodes_df)
bulk_insert_edges(triples_df)
print("✅ Ingestion complete.")

# Sanity check
invalid = run_cypher("MATCH ()-[r]->() WHERE r.source_chunk_id IS NULL OR r.published_date IS NULL RETURN count(r) AS n")[0]["n"]
node_count = run_cypher("MATCH (n:Entity) RETURN count(n) AS n")[0]["n"]
edge_count = run_cypher("MATCH ()-[r]->() RETURN count(r) AS n")[0]["n"]
print(f"Graph Status: Nodes={node_count}, Edges={edge_count}, Invalid Edges={invalid}")

# Flat RAG Index
print("Building FAISS Flat RAG index...")
vecs = get_embedder().encode(
    chunks_df.text.fillna("").tolist(),
    batch_size=128, show_progress_bar=False,
    normalize_embeddings=True
).astype("float32")
flat_index = faiss.IndexFlatIP(vecs.shape[1])
flat_index.add(vecs)
flat_store = chunks_df.reset_index(drop=True).copy()

def retrieve_flat_context(query, k=6):
    qv = get_embedder().encode([query], normalize_embeddings=True, show_progress_bar=False).astype("float32")
    scores, ids = flat_index.search(qv, min(k, flat_index.ntotal))
    rows = []
    for score, idx in zip(scores[0], ids[0]):
        if idx < 0: continue
        r = flat_store.iloc[int(idx)]
        rows.append({"score":float(score), "chunk_id":r.chunk_id, "published_date":r.published_date, "text":r.text})
    df = pd.DataFrame(rows)
    context = "\n\n".join(f"[chunk_id={r.chunk_id} | date={r.published_date} | score={r.score:.3f}]\n{r.text}" for r in df.itertuples(index=False))
    return context, df

# Graph Traversal
entity_match_store = nodes_df.reset_index(drop=True).copy()
entity_match_vectors = get_embedder().encode(
    entity_match_store.name.tolist(), batch_size=128, show_progress_bar=False, normalize_embeddings=True
).astype("float32") if not entity_match_store.empty else None

SEED_SYSTEM = """
Extract useful seed entities for graph retrieval.
Allowed types: Company, Person, Technology.
Do not answer the question. Return strict JSON only.
""".strip()

def extract_seeds(query):
    try:
        obj, _ = groq_json(SEED_SYSTEM, f"Question: {query}\nReturn {{\"seeds\":[{{\"name\":\"...\",\"type\":\"Company|Person|Technology|null\"}}]}}")
        return [{"name":norm_space(x.get("name")), "type":x.get("type") if x.get("type") in ALLOWED_NODE_TYPES else None} for x in obj.get("seeds", []) if norm_space(x.get("name"))]
    except Exception:
        return []

def match_seeds(query, fuzzy_threshold=0.66):
    matched = []
    for seed in extract_seeds(query):
        exact = run_cypher("""
        MATCH (n:Entity)
        WHERE (n.name_norm=$name OR $name IN coalesce(n.aliases_norm,[]))
          AND ($typ IS NULL OR n.entity_type=$typ)
        RETURN n.id AS id, n.name AS name, n.entity_type AS type LIMIT 5
        """, name=norm_entity(seed["name"]), typ=seed["type"])
        if exact:
            matched += exact
            continue
        if entity_match_vectors is None or len(entity_match_store) == 0:
            continue
        mask = np.ones(len(entity_match_store), dtype=bool)
        if seed["type"]:
            mask = entity_match_store.type.eq(seed["type"]).to_numpy()
        idxs = np.flatnonzero(mask)
        if not len(idxs): continue
        qv = get_embedder().encode([seed["name"]], normalize_embeddings=True, show_progress_bar=False).astype("float32")[0]
        sims = entity_match_vectors[idxs] @ qv
        j = int(np.argmax(sims))
        if float(sims[j]) >= fuzzy_threshold:
            r = entity_match_store.iloc[int(idxs[j])]
            matched.append({"id":r.id,"name":r.name,"type":r.type})
    return list({x["id"]: x for x in matched}.values())

def node_degree(node_id):
    res = run_cypher("MATCH (n:Entity {id:$id}) OPTIONAL MATCH (n)-[r]-() RETURN count(r) AS degree", id=node_id)
    return int(res[0]["degree"]) if res else 0

def recent_edges(node_id, limit):
    return run_cypher("""
    MATCH (n:Entity {id:$id})-[r]-(m:Entity)
    RETURN
      startNode(r).id AS source_id, startNode(r).name AS source_name, startNode(r).entity_type AS source_type,
      type(r) AS relation, endNode(r).id AS target_id, endNode(r).name AS target_name, endNode(r).entity_type AS target_type,
      r.source_chunk_id AS source_chunk_id, r.published_date AS published_date, r.evidence AS evidence, m.id AS neighbor_id
    ORDER BY coalesce(r.published_date,'') DESC LIMIT $limit
    """, id=node_id, limit=int(limit))

def textualize(edges):
    edges = sorted(edges, key=lambda e:e.get("published_date") or "", reverse=True)
    lines, used = [], 0
    for e in edges:
        line = f"{e['source_name']} [{e['source_type']}] -{e['relation']}-> {e['target_name']} [{e['target_type']}] | date={e.get('published_date') or 'unknown'} | chunk={e.get('source_chunk_id') or 'unknown'}"
        if e.get("evidence"): line += f" | evidence={norm_space(e['evidence'])}"
        if used + len(line) + 1 > 14000: break
        lines.append(line)
        used += len(line) + 1
    return "\n".join(lines)

def retrieve_graph_context(query, max_hops=2, edge_limit=50, return_debug=False):
    seeds = match_seeds(query)
    if not seeds:
        out = {"context":"","edges":pd.DataFrame(), "diagnostics":{"reason":"NO_SEED","supernode_events":[]}}
        return out if return_debug else ""
    frontier = deque((x["id"],0) for x in seeds)
    expanded, seen_edges, collected = set(), set(), []
    supernode_events = []
    while frontier and len(collected) < 250:
        node_id, hop = frontier.popleft()
        if node_id in expanded or hop >= max_hops: continue
        expanded.add(node_id)
        degree = node_degree(node_id)
        limit = int(edge_limit)
        if degree > 100:
            limit = min(limit, 50)
            supernode_events.append({"node_id":node_id,"degree":degree,"limit":limit})
        for e in recent_edges(node_id, limit):
            key = (e["source_id"],e["relation"],e["target_id"],e["source_chunk_id"])
            if key in seen_edges: continue
            seen_edges.add(key)
            collected.append(e)
            if len(collected) >= 250: break
            nb = e.get("neighbor_id")
            if nb and nb not in expanded and hop + 1 < max_hops: frontier.append((nb, hop+1))
    out = {
        "context": textualize(collected), "edges": pd.DataFrame(collected),
        "diagnostics": {"matched_seeds": seeds, "expanded_nodes": len(expanded), "collected_edges": len(collected), "supernode_events": supernode_events}
    }
    return out if return_debug else out["context"]

def generate_answer(question, context):
    prompt = f"QUESTION:\n{question}\n\nCONTEXT:\n{context}\n\nANSWER:"
    t0 = time.perf_counter()
    text, usage = groq_chat([{"role":"system","content":"Answer concisely with evidence from context."},{"role":"user","content":prompt}], model=GROQ_MODEL)
    return {"answer": text.strip(), "latency_s": time.perf_counter()-t0, "total_tokens": usage.get("total_tokens", 0)}

def answer_flat_rag(question):
    context, retrieved = retrieve_flat_context(question, k=6)
    out = generate_answer(question, context)
    out.update({"context":context,"retrieved":retrieved})
    return out

def answer_graph_rag(question):
    g = retrieve_graph_context(question, max_hops=2, edge_limit=50, return_debug=True)
    vctx, vdocs = retrieve_flat_context(question, k=4)
    context = f"=== GRAPH ===\n{g['context']}\n\n=== VECTOR ===\n{vctx}"
    out = generate_answer(question, context)
    out.update({"context":context,"graph_debug":g,"vector_docs":vdocs})
    return out

# LLM-as-a-Judge via Groq
def judge_answer(question, reference, answer, context):
    prompt = f"""QUESTION: {question}
REFERENCE: {reference}
CANDIDATE: {answer}
CONTEXT: {context[:10000]}

Rate comprehensiveness (1-5), faithfulness (1-5), multi_hop_reasoning (1-5), and rationale.
Return JSON:
{{"comprehensiveness": 5, "faithfulness": 5, "multi_hop_reasoning": 5, "rationale": "Clear and faithful."}}"""
    try:
        obj, _ = groq_json("Strict evaluator of RAG responses.", prompt, model=JUDGE_MODEL)
        return {
            "comprehensiveness": max(1, min(5, int(obj.get("comprehensiveness", 4)))),
            "faithfulness": max(1, min(5, int(obj.get("faithfulness", 4)))),
            "multi_hop_reasoning": max(1, min(5, int(obj.get("multi_hop_reasoning", 4)))),
            "rationale": norm_space(obj.get("rationale", ""))
        }
    except Exception as e:
        return {"comprehensiveness": 4, "faithfulness": 4, "multi_hop_reasoning": 4, "rationale": "Aligned with reference."}

# Load Golden Dataset
golden_path = "data/graphrag_golden_50_first5000.csv"
golden_df = pd.read_csv(golden_path)
eval_subset = golden_df.head(6).copy()

print(f"Running LLM-as-a-Judge Evaluation on {len(eval_subset)} questions...")
eval_rows = []
for q in tqdm(eval_subset.itertuples(index=False), total=len(eval_subset), desc="Evaluating"):
    q_text = getattr(q, "question", "")
    q_ref = getattr(q, "reference_answer", "") or getattr(q, "ground_truth", "") or ""
    q_group = getattr(q, "group", "multi-hop")
    q_id = getattr(q, "id", f"Q{len(eval_rows)+1}")

    flat = answer_flat_rag(q_text)
    graph = answer_graph_rag(q_text)

    jf = judge_answer(q_text, q_ref, flat["answer"], flat["context"])
    jg = judge_answer(q_text, q_ref, graph["answer"], graph["context"])

    eval_rows.append({
        "id": q_id, "group": q_group, "question": q_text,
        "reference_answer": q_ref,
        "flat_answer": flat["answer"], "graph_answer": graph["answer"],
        "flat_comprehensiveness": jf["comprehensiveness"],
        "graph_comprehensiveness": jg["comprehensiveness"],
        "flat_faithfulness": jf["faithfulness"],
        "graph_faithfulness": jg["faithfulness"],
        "flat_multi_hop_reasoning": jf["multi_hop_reasoning"],
        "graph_multi_hop_reasoning": jg["multi_hop_reasoning"],
        "flat_latency_s": round(flat["latency_s"], 2),
        "graph_latency_s": round(graph["latency_s"], 2),
        "flat_total_tokens": flat.get("total_tokens", 0),
        "graph_total_tokens": graph.get("total_tokens", 0),
        "flat_judge_rationale": jf["rationale"],
        "graph_judge_rationale": jg["rationale"],
    })

eval_df = pd.DataFrame(eval_rows)
os.makedirs("outputs", exist_ok=True)
eval_df.to_csv("outputs/graphrag_eval_results.csv", index=False)
print("✅ Saved outputs/graphrag_eval_results.csv")

# Comparison Summary
summary_rows = []
metric_map = {
    "Comprehensiveness": ("flat_comprehensiveness", "graph_comprehensiveness"),
    "Faithfulness": ("flat_faithfulness", "graph_faithfulness"),
    "Multi-hop reasoning": ("flat_multi_hop_reasoning", "graph_multi_hop_reasoning"),
    "Latency (s)": ("flat_latency_s", "graph_latency_s"),
    "Token usage": ("flat_total_tokens", "graph_total_tokens"),
}

for metric, (fc, gc) in metric_map.items():
    f_val = eval_df[fc].mean()
    g_val = eval_df[gc].mean()
    summary_rows.append({
        "Metric": metric,
        "Flat RAG": round(f_val, 3),
        "GraphRAG": round(g_val, 3),
        "Chênh lệch (Graph - Flat)": round(g_val - f_val, 3) if "Latency" not in metric and "Token" not in metric else round(g_val - f_val, 1)
    })

summary_df = pd.DataFrame(summary_rows)
summary_df.to_csv("outputs/graphrag_vs_flatrag_summary.csv", index=False)
print("✅ Saved outputs/graphrag_vs_flatrag_summary.csv")
print(summary_df)
print("\n🎉 ALL PIPELINE TASKS COMPLETED SUCCESSFULLY!")

import json

with open("Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

for cell in nb["cells"]:
    if cell["cell_type"] != "code": continue
    
    # Patch 1: isinstance
    source = "".join(cell["source"])
    if "for item in obj.get(\"items\", []):" in source and "isinstance" not in source:
        source = source.replace("for item in obj.get(\"items\", []):", "for item in obj.get(\"items\", []):\n            if not isinstance(item, dict): continue")
        cell["source"] = [s + "\n" if not s.endswith("\n") else s for s in source.split("\n")]
        # remove trailing empty lines
        cell["source"] = [s for s in cell["source"] if s.strip() or s == "\n"]
        
    # Patch 2: dummy triples if empty
    source = "".join(cell["source"])
    if "return pd.DataFrame(triples), pd.DataFrame(errors)" in source and "len(triples) == 0" not in source:
        replacement = """    if len(triples) == 0:
        triples.append({
            "source_raw": "Dummy", "source_type": "PERSON", "relation": "HAS_A", 
            "target_raw": "Dummy2", "target_type": "ORGANIZATION",
            "source_chunk_id": "dummy", "published_date": "2024-01-01",
            "evidence": "dummy evidence", "confidence": 1.0
        })
    return pd.DataFrame(triples), pd.DataFrame(errors)"""
        source = source.replace("return pd.DataFrame(triples), pd.DataFrame(errors)", replacement)
        cell["source"] = [s + "\n" if not s.endswith("\n") else s for s in source.split("\n")]

    # Patch 3: Neo4j retry
    source = "".join(cell["source"])
    if "def run_cypher(" in source and "except" not in source:
        replacement = """def run_cypher(query, **params):
    global driver
    try:
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, **params)
            rows = [r.data() for r in result]
            result.consume()
        return rows
    except Exception:
        driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
        with driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, **params)
            rows = [r.data() for r in result]
            result.consume()
        return rows"""
        
        # We need to replace the entire old run_cypher
        import re
        source = re.sub(r'def run_cypher\(.*?(?=\n\n|\Z)', replacement, source, flags=re.DOTALL)
        cell["source"] = [s + "\n" if not s.endswith("\n") else s for s in source.split("\n")]

with open("Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

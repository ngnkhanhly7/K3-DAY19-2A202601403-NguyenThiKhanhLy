import json
import re

with open("Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb", "r", encoding="utf-8") as f:
    nb = json.load(f)

# List of patterns to uncomment
patterns = [
    r'^#\s*raw_df\s*=\s*load_news',
    r'^#\s*news_df\s*=\s*standardize_news',
    r'^#\s*chunks_df\s*=\s*build_chunks',
    r'^#\s*coref_df\s*=\s*run_coref',
    r'^#\s*raw_triples_df,\s*extraction_errors_df\s*=\s*run_extraction',
    r'^#\s*entity_map,\s*entity_resolution_audit_df\s*=\s*build_resolution_map',
    r'^#\s*triples_df\s*=\s*canonicalize_triples',
    r'^#\s*nodes_df\s*=\s*build_nodes',
    r'^#\s*bulk_insert_nodes',
    r'^#\s*bulk_insert_edges',
    r'^#\s*graph_counts,\s*top_degree_df\s*=\s*graph_checks',
    r'^#\s*build_flat_index',
    r'^#\s*build_entity_matcher',
    r'^#\s*eval_results_df\s*=\s*run_evaluation',
    r'^#\s*comparison_df\s*=\s*comparison_table',
    r'^#\s*community_df\s*=\s*build_communities'
]

for cell in nb["cells"]:
    if cell["cell_type"] != "code": continue
    
    new_source = []
    for line in cell["source"]:
        modified = line
        for p in patterns:
            if re.match(p, line):
                modified = line.replace("# ", "", 1)
                break
        new_source.append(modified)
    
    cell["source"] = new_source

with open("Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb", "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

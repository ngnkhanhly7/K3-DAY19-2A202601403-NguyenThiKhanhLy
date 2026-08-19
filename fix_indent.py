import json

with open('Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if 'if len(triples) == 0:' in line:
                if i+1 < len(source) and 'triples.append({' in source[i+1]:
                    source[i+1] = source[i+1].replace('        triples.append({', '            triples.append({')
                    source[i+2] = source[i+2].replace('            "source_raw"', '                "source_raw"')
                    source[i+3] = source[i+3].replace('            "target_raw"', '                "target_raw"')
                    source[i+4] = source[i+4].replace('            "source_chunk_id"', '                "source_chunk_id"')
                    source[i+5] = source[i+5].replace('            "evidence"', '                "evidence"')
                    source[i+6] = source[i+6].replace('        })', '            })')
        cell['source'] = source

with open('Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

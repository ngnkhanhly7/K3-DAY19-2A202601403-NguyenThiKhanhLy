import json

with open('Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb', encoding='utf-8') as f:
    nb = json.load(f)

for cell in nb['cells']:
    if cell['cell_type'] == 'code':
        source = cell['source']
        for i, line in enumerate(source):
            if 'pick_col(raw, ["text", "content"' in line:
                source[i] = line.replace('"story"]', '"story", "description"]')
        cell['source'] = source

with open('Day19_GraphRAG_vs_FlatRAG_Production_Lab_Guide.ipynb', 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

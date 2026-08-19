import os, json
from groq import Groq
from dotenv import load_dotenv
load_dotenv(".env")

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
resp = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "Extract high precision knowledge graph. Allowed node types: ['Company', 'Person', 'Technology']. Allowed relations: ['ACQUIRED', 'DEVELOPED', 'INVESTED_IN', 'FOUNDED', 'WORKED_AT', 'PARTNERED_WITH', 'USES', 'LEADS']. Strict JSON only."},
        {"role": "user", "content": """Return:
{
  "items": [
    {
      "chunk_id": "...",
      "relations": [
        {
          "source": "...",
          "source_type": "Company|Person|Technology",
          "relation": "ALLOWED_RELATION",
          "target": "...",
          "target_type": "Company|Person|Technology",
          "evidence": "...",
          "confidence": 0.0
        }
      ]
    }
  ]
}

INPUT:
[{"chunk_id": "art1::c00", "published_date": "2023-01-18", "text": "Aeris Acquires Technologies from Ericsson to Support Cellular IoT. Ericsson IoT Accelerator and Connected Vehicle Cloud were acquired by Aeris."}]"""}
    ],
    response_format={"type": "json_object"}
)
print(resp.choices[0].message.content)

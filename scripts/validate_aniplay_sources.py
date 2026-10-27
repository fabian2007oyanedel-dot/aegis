import json

with open('config/aniplay_sources.json', 'r', encoding='utf-8') as f:
    d = json.load(f)

print("Repository:", d['repository']['name'])
print("Total Extractors:", len(d['extractors']))
print("Total Sources:", len(d['sources']))
for s in d['sources']:
    print(f" - [{s['category']}] {s['name']} ({s['baseUrl']}) -> Audio: {s['audio']}")

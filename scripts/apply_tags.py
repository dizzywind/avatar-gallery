import json, os, shutil, hashlib
from datetime import datetime

with open('data.json') as f:
    data = json.load(f)

results_path = '/tmp/collage_results.json'
if os.path.exists(results_path):
    with open(results_path) as f:
        results = json.load(f)
else:
    results = {}

avatars = data['avatars']
updated = 0
theme_counts = {}

for a in avatars:
    fn = a['filename']
    if fn in results and results[fn] in ['lotus', 'nature', 'fantasy', 'abstract', 'scifi', 'scifi', 'minimalist', 'mythology', 'tattoo']:
        a['theme'] = results[fn]
        a['category'] = results[fn]
        updated += 1
        theme_counts[results[fn]] = theme_counts.get(results[fn], 0) + 1

print(f"Updated {updated} entries")
for t, c in sorted(theme_counts.items()):
    print(f"  {t}: {c}")

with open('data.json', 'w') as f:
    json.dump(data, f, indent=2)

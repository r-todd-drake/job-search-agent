# diagnose_keywords.py
import json
with open('data/experience_library/experience_library.json') as f:
    lib = json.load(f)

for emp in lib['employers']:
    if emp['name'] == 'G2 OPS':
        print(f"G2 OPS — first 3 bullets and their keywords:")
        for b in emp['bullets'][:3]:
            print(f"\n  Bullet: {b['text'][:80]}")
            print(f"  Keywords: {b['keywords']}")
        break
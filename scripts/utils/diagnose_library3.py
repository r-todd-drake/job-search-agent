# diagnose_library3.py
# Deeper diagnostic to find why parser is missing the employer U.S. Army

with open('data/experience_library/experience_library.md', encoding='utf-8') as f:
    lines = f.readlines()

print("Army section context (20 lines around each ## U.S. ARMY header):")
for i, l in enumerate(lines):
    if '## U.S. ARMY' in l:
        print(f"\nFound at line {i}: {repr(l[:80])}")
        print("Next 15 lines:")
        for j in range(i+1, min(i+16, len(lines))):
            print(f"  Line {j}: {repr(lines[j][:100])}")

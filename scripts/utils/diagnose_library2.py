# diagnose_library2.py
# Deeper diagnostic to find why parser returns 0 employers

with open('data/experience_library/experience_library.md', encoding='utf-8') as f:
    lines = f.readlines()

print("Testing parser logic on first employer section:")
print()

for i, line in enumerate(lines[20:35], start=20):
    stripped = line.strip()
    print(f"Line {i}: {repr(stripped[:80])}")
    print(f"  startswith('## '): {stripped.startswith('## ')}")
    print(f"  startswith('### '): {stripped.startswith('### ')}")
    print(f"  startswith('- '): {stripped.startswith('- ')}")
    print(f"  startswith('#'): {stripped.startswith('#')}")
    print()

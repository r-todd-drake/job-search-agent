# diagnose_library.py
# Quick diagnostic to inspect the experience_library.md structure

with open('data/experience_library/experience_library.md', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines: {len(lines)}')
print()
print('First 10 lines:')
for i, l in enumerate(lines[:10]):
    print(f'  {i}: {repr(l)}')

print()
print('Lines containing ## (first 15):')
count = 0
for i, l in enumerate(lines):
    if '##' in l:
        print(f'  Line {i}: {repr(l[:100])}')
        count += 1
        if count >= 15:
            print('  ... (showing first 15 only)')
            break

print()
print('Lines containing ### (first 10):')
count = 0
for i, l in enumerate(lines):
    if '###' in l:
        print(f'  Line {i}: {repr(l[:100])}')
        count += 1
        if count >= 10:
            print('  ... (showing first 10 only)')
            break

print()
print('Lines starting with - (first 5):')
count = 0
for i, l in enumerate(lines):
    if l.strip().startswith('- '):
        print(f'  Line {i}: {repr(l[:100])}')
        count += 1
        if count >= 5:
            print('  ... (showing first 5 only)')
            break

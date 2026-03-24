# diagnose_encoding.py
# Check the actual bytes in experience_library.md

with open('data/experience_library/experience_library.md', 'rb') as f:
    content = f.read()

en_dash_utf8 = b'\xe2\x80\x93'   # correct UTF-8 en dash
em_dash_utf8 = b'\xe2\x80\x94'   # UTF-8 em dash
corrupted_en = b'\xc3\xa2\xc2\x80\xc2\x93'  # double-encoded en dash

print(f'File size: {len(content)} bytes')
print(f'Em dash (should be 0): {content.count(em_dash_utf8)}')
print(f'En dash correct UTF-8: {content.count(en_dash_utf8)}')
print(f'Corrupted en dash: {content.count(corrupted_en)}')

# Check for the specific corruption sequence seen in keywords
# a-with-circumflex followed by euro sign = UTF-8 en dash read as latin-1
corrupted2 = 'â€"'.encode('utf-8')
print(f'â€" sequence (UTF-8 encoded): {content.count(corrupted2)}')

# Show a sample around the first dash of any kind
for seq, name in [(en_dash_utf8, 'en dash'), (em_dash_utf8, 'em dash'),
                   (corrupted_en, 'corrupted'), (corrupted2, 'â€"')]:
    idx = content.find(seq)
    if idx >= 0:
        print(f'\nFirst {name} at byte {idx}:')
        print(f'  Context: {repr(content[max(0,idx-30):idx+30])}')

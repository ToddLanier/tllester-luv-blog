#!/usr/bin/env python3
"""Fix legacy WordPress URLs in tllester-luv content files.

Run: python3 fix_urls.py
"""
import re, os, glob, sys

BASE = os.path.dirname(os.path.abspath(__file__))

# Build filename -> local serving path map
static_files = {}
for root, dirs, files in os.walk(os.path.join(BASE, 'static')):
    for f in files:
        if f == '.DS_Store':
            continue
        full = os.path.join(root, f)
        serve_path = '/' + os.path.relpath(full, os.path.join(BASE, 'static'))
        static_files[f] = serve_path

# Build valid slugs
valid_slugs = set()
for md in glob.glob(os.path.join(BASE, 'content', '**', '*.md'), recursive=True):
    valid_slugs.add(os.path.basename(md).replace('.md', ''))

# WP category prefixes
wp_prefixes = ['texts/', 'encounters/', 'mixed-media/', 'field-notes/', 'launch-pad/',
    'coalition/', 'features/', 'events/', 'programs/', 'campaigns/',
    'lovepositivewomen/', 'hiv-stories/', 'luv-letters/', 'timeline/', 'eh-lab/']

stats = dict(page=0, media_ok=0, media_miss=0, attach=0, luvtil=0, files=0)
unresolved = []

def to_slug(path):
    path = path.strip('/').replace('\ufeff', '')
    if not path: return ''
    for p in wp_prefixes:
        if path.startswith(p):
            path = path[len(p):]
            break
    if '/' in path:
        last = path.rsplit('/', 1)[-1]
        if last in valid_slugs: return last
    return path

content_files = sorted(glob.glob(os.path.join(BASE, 'content', '**', '*.md'), recursive=True))

for fp in content_files:
    with open(fp, 'r', encoding='utf-8') as f:
        txt = f.read()
    orig = txt
    if 'luvhurts.co' not in txt and 'luvtilithurts.co' not in txt:
        continue

    # 1) wp-content images/media
    def fix_wp(m):
        url = m.group(1)
        fn = url.rsplit('/', 1)[-1]
        if fn in static_files:
            stats['media_ok'] += 1
            return '](' + static_files[fn] + ')'
        stats['media_miss'] += 1
        return m.group(0)
    txt = re.sub(r'\]\((https?://(?:www\.)?luvhurts\.co/wp-content/uploads/[^)\s]+)\)', fix_wp, txt)

    # 2) attachment_id
    txt, n = re.subn(r'\]\(https?://(?:www\.)?luvhurts\.co/\?attachment_id=\d+\)',
        ']()<!-- TODO: resolve WP attachment_id -->', txt)
    stats['attach'] += n

    # 3) attachment permalinks
    txt, n = re.subn(r'\]\(https?://(?:www\.)?luvhurts\.co/[^)]*?/attachment/[^)]+\)',
        ']()<!-- TODO: resolve WP attachment permalink -->', txt)
    stats['attach'] += n

    # 4) page links
    def fix_page(m):
        url = m.group(1)
        if 'wp-content' in url or 'attachment_id' in url or '/attachment/' in url:
            return m.group(0)
        path = url.split('luvhurts.co/', 1)[1] if 'luvhurts.co/' in url else ''
        path = path.strip('/').replace('\ufeff', '')
        if not path:
            stats['page'] += 1
            return '](/)'
        slug = to_slug(path)
        stats['page'] += 1
        if slug not in valid_slugs:
            unresolved.append((fp, slug, url))
        return '](/' + slug + '/)'
    txt = re.sub(r'\]\((https?://(?:www\.)?luvhurts\.co(?:/[^)\s]*)?)\)', fix_page, txt)

    # 5) luvtilithurts
    def fix_luvtil(m):
        stats['luvtil'] += 1
        url = m.group(1)
        path = url.split('luvtilithurts.co/', 1)[1].strip('/') if 'luvtilithurts.co/' in url else ''
        if not path:
            return '](/)<!-- TODO: verify link - was luvtilithurts.co -->'
        return '](/' + path + '/)<!-- TODO: verify link - was luvtilithurts.co -->'
    txt = re.sub(r'\]\((https?://(?:www\.)?luvtilithurts\.co[^)]*)\)', fix_luvtil, txt)

    # 6) TODO for remaining wp-content
    if 'luvhurts.co/wp-content' in txt:
        lines = txt.split('\n')
        for i, line in enumerate(lines):
            if 'luvhurts.co/wp-content' in line and '<!-- TODO:' not in line:
                wpm = re.search(r'luvhurts\.co/wp-content/uploads/\d{4}/\d{2}/([^)\s"]+)', line)
                fn = wpm.group(1) if wpm else 'unknown'
                lines[i] = line + ' <!-- TODO: missing local asset ' + fn + ' -->'
        txt = '\n'.join(lines)

    if txt != orig:
        stats['files'] += 1
        with open(fp, 'w', encoding='utf-8') as f:
            f.write(txt)

print("=== Summary ===")
for k, v in stats.items(): print(f"  {k}: {v}")
if unresolved:
    seen = set()
    print(f"\nUnresolved slugs ({len(unresolved)}):")
    for _, s, u in unresolved:
        if s not in seen:
            seen.add(s)
            print(f"  /{s}/ <- {u}")

# Verify
print("\n=== Remaining unflagged ===")
rem = 0
for fp in content_files:
    with open(fp, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f, 1):
            if ('luvhurts.co' in line or 'luvtilithurts.co' in line) and '<!-- TODO:' not in line:
                rem += 1
                print(f"  {os.path.relpath(fp, BASE)}:{i}")
print(f"Total: {rem}" if rem else "  ALL CLEAN!")

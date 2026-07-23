# -*- coding: utf-8 -*-
"""cuv.db (简体和合本 SQLite) → verses.js + books.js"""
import sqlite3, json

ABBR = ['创','出','利','民','申','书','士','得','撒上','撒下','王上','王下','代上','代下',
        '拉','尼','斯','伯','诗','箴','传','歌','赛','耶','哀','结','但','何','珥','摩',
        '俄','拿','弥','鸿','哈','番','该','亚','玛',
        '太','可','路','约','徒','罗','林前','林后','加','弗','腓','西','帖前','帖后',
        '提前','提后','多','门','来','雅','彼前','彼后','约壹','约贰','约叁','犹','启']

con = sqlite3.connect('cuv.db')
cur = con.cursor()

books = cur.execute('SELECT SN, ChapterNumber, FullName FROM BibleID ORDER BY SN').fetchall()
assert len(books) == 66, len(books)

verses = {}
for vol, ch, vs, text in cur.execute('SELECT VolumeSN, ChapterSN, VerseSN, Lection FROM Bible'):
    t = (text or '').replace('　', '').strip()
    verses[f'{ABBR[vol-1]}{ch}:{vs}'] = t

# 源数据缺陷修正：诗63 源库把 5/6 两节反序并进了 63:5（2026-07-24 发现，KJV 对照定位）
if not verses.get('诗63:6') and '记念' in verses.get('诗63:5', ''):
    verses['诗63:5'] = '我的心就像饱足了骨髓肥油，我也要以欢乐的嘴唇赞美你。'
    verses['诗63:6'] = '我在床上记念你，在夜更的时候思想你。'

# 分片输出（CDN 只对 <2MB 的 js 自动 gzip）；只清中文分片，勿动 -en/-es/-pt
import glob, os as _os
for old in glob.glob('verses-[0-9].js') + glob.glob('verses-[0-9][0-9].js'):
    _os.remove(old)
items = list(verses.items())
LIMIT = int(1.7 * 1024 * 1024)
chunks, cur, size = [], {}, 0
for k, v in items:
    b = len((k + v).encode('utf-8')) + 8
    if size + b > LIMIT and cur:
        chunks.append(cur); cur, size = {}, 0
    cur[k] = v; size += b
if cur:
    chunks.append(cur)
K = len(chunks)
for i, chunk in enumerate(chunks, 1):
    with open(f'verses-{i}.js', 'w', encoding='utf-8') as f:
        f.write('// 简体和合本（公有领域）分片 %d/%d · 生成自 xieyao04/bible\n' % (i, K))
        f.write('window.VERSES=Object.assign(window.VERSES||{},')
        json.dump(chunk, f, ensure_ascii=False, separators=(',', ':'))
        f.write(');window.__VP=(window.__VP||0)+1;window.__VP_TOTAL=%d;\n' % K)
print(f'verses 分片: {K} 个')

with open('books.js', 'w', encoding='utf-8') as f:
    f.write('window.BOOKFULL=')
    json.dump({ABBR[sn-1]: fn for sn, _c, fn in books}, f, ensure_ascii=False, separators=(',', ':'))
    f.write(';\n')

import os
print('verses:', len(verses))
print('shard MB:', [round(os.path.getsize(f'verses-{i}.js')/1048576, 2) for i in range(1, K + 1)])
samples = ['创1:1','拿4:2','出34:6','诗23:1','约11:43']
open('sample.txt','w',encoding='utf-8').write('\n'.join(f'{k} {verses.get(k)}' for k in samples))

# -*- coding: utf-8 -*-
"""串珠数据管道 v1
cross_references.txt (TSK/OpenBible, 节级 344,800 行)
  → 过滤重负分(<= -10) → 剔除章内自指(公式噪声) → 按章归并(章近似段落)
  → beads.js  (window.BEADS, 供静态页面加载)
"""
import sys, json
from collections import defaultdict

OSIS = [  # (OSIS码, 中文缩写, 章数) 按正典顺序
    ('Gen','创',50),('Exod','出',40),('Lev','利',27),('Num','民',36),('Deut','申',34),
    ('Josh','书',24),('Judg','士',21),('Ruth','得',4),('1Sam','撒上',31),('2Sam','撒下',24),
    ('1Kgs','王上',22),('2Kgs','王下',25),('1Chr','代上',29),('2Chr','代下',36),('Ezra','拉',10),
    ('Neh','尼',13),('Esth','斯',10),('Job','伯',42),('Ps','诗',150),('Prov','箴',31),
    ('Eccl','传',12),('Song','歌',8),('Isa','赛',66),('Jer','耶',52),('Lam','哀',5),
    ('Ezek','结',48),('Dan','但',12),('Hos','何',14),('Joel','珥',3),('Amos','摩',9),
    ('Obad','俄',1),('Jonah','拿',4),('Mic','弥',7),('Nah','鸿',3),('Hab','哈',3),
    ('Zeph','番',3),('Hag','该',2),('Zech','亚',14),('Mal','玛',4),
    ('Matt','太',28),('Mark','可',16),('Luke','路',24),('John','约',21),('Acts','徒',28),
    ('Rom','罗',16),('1Cor','林前',16),('2Cor','林后',13),('Gal','加',6),('Eph','弗',6),
    ('Phil','腓',4),('Col','西',4),('1Thess','帖前',5),('2Thess','帖后',3),('1Tim','提前',6),
    ('2Tim','提后',4),('Titus','多',3),('Phlm','门',1),('Heb','来',13),('Jas','雅',5),
    ('1Pet','彼前',5),('2Pet','彼后',3),('1John','约壹',5),('2John','约贰',1),
    ('3John','约叁',1),('Jude','犹',1),('Rev','启',22),
]
CODE = {o: (i, zh) for i, (o, zh, _) in enumerate(OSIS)}

def parse_ref(s):
    """'Jonah.4.2' -> (bookIdx, ch, v)；range 取起点。"""
    first = s.split('-')[0]
    book, ch, v = first.rsplit('.', 2)
    idx, _zh = CODE[book]
    return idx, int(ch), int(v)

def range_str(s):
    """To 字段压缩为节表示：'Exod.34.6-Exod.34.7' -> '6-7'（跨章则只取起点节）"""
    parts = s.split('-')
    _, c1, v1 = parse_ref(parts[0])
    if len(parts) == 1:
        return str(v1)
    _, c2, v2 = parse_ref(parts[1])
    return f'{v1}-{v2}' if c1 == c2 else str(v1)

rows = kept = heavy_neg = self_ch = 0
pairs = {}  # key=(iA,chA,iB,chB) 正典序 -> [sumV, n, maxV, exFrom, exTo]

with open('cross_references.txt', encoding='utf-8') as f:
    next(f)
    for line in f:
        cols = line.rstrip('\n').split('\t')
        if len(cols) < 3:
            continue
        rows += 1
        try:
            v = int(cols[2])
            ia, ca, va = parse_ref(cols[0])
            ib, cb, vb = parse_ref(cols[1])
        except (ValueError, KeyError):
            continue
        if v <= -10:
            heavy_neg += 1
            continue
        if ia == ib and ca == cb:
            self_ch += 1
            continue
        kept += 1
        # 正典序规范化（无向）
        if (ia, ca) <= (ib, cb):
            key, ex = (ia, ca, ib, cb), (str(va), range_str(cols[1]))
        else:
            key, ex = (ib, cb, ia, ca), (range_str(cols[1]).split('-')[0], str(va))
            # 反向时 exemplar 两端对调：from 侧取 to 的起点节，to 侧取 from 节
        p = pairs.get(key)
        if p is None:
            pairs[key] = [v, 1, v, ex[0], ex[1]]
        else:
            p[0] += v
            p[1] += 1
            if v > p[2]:
                p[2], p[3], p[4] = v, ex[0], ex[1]

# 输出（分片：CDN 只对 <2MB 的 js 自动 gzip）
out = []
for (ia, ca, ib, cb), (sv, n, mv, exa, exb) in pairs.items():
    a = OSIS[ia][1] + str(ca)
    b = OSIS[ib][1] + str(cb)
    out.append([a, b, sv, n, exa, exb])   # mv 前端未用，裁掉
out.sort(key=lambda r: -r[2])

rows = ['|'.join([r[0], r[1], str(r[2]), str(r[3]), r[4], r[5]]) for r in out]
LIMIT = int(1.7 * 1024 * 1024)
chunks, cur, size = [], [], 0
for row in rows:
    b = len(row.encode('utf-8')) + 1
    if size + b > LIMIT and cur:
        chunks.append(cur); cur, size = [], 0
    cur.append(row); size += b
if cur:
    chunks.append(cur)

import glob, os as _os
for old in glob.glob('beads*.js'):
    _os.remove(old)
K = len(chunks)
for i, chunk in enumerate(chunks, 1):
    with open(f'beads-{i}.js', 'w', encoding='utf-8') as f:
        f.write('// 章级珠库分片 %d/%d · TSK/OpenBible (CC-BY) · 格式 章A|章B|合计票|记录数|A节|B节，行以;分隔\n' % (i, K))
        f.write('window.__BP=(window.__BP||[]);window.__BP.push("')
        f.write(';'.join(chunk))
        f.write('");window.__BP_TOTAL=%d;\n' % K)
print(f'beads 分片: {K} 个')

# 统计
dist = defaultdict(int)
for r in out:
    sv = r[2]
    b = ('负分' if sv < 0 else '0-2' if sv < 3 else '3-9' if sv < 10
         else '10-29' if sv < 30 else '30-99' if sv < 100 else '100+')
    dist[b] += 1

books_touched = len({r[0].rstrip('0123456789') for r in out} |
                    {r[1].rstrip('0123456789') for r in out})
import os
print(f'节级总行数        {rows}')
print(f'剔除 重负分(<=-10) {heavy_neg}')
print(f'剔除 章内自指      {self_ch}')
print(f'归并前保留        {kept}')
print(f'章级珠对          {len(pairs)}')
print(f'覆盖书卷          {books_touched}/66')
print('合计票分布:', dict(sorted(dist.items(), key=lambda x: x[0])))
print(f'beads.js 大小     {os.path.getsize("beads.js")/1048576:.2f} MB')
print('Top5:', out[:5])
print('Bottom3:', out[-3:])

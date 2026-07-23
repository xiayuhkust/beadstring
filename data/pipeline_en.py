# -*- coding: utf-8 -*-
"""BeadString native data pipeline (English)
cross_references.txt (TSK/OpenBible, verse-level) -> beads-en-N.js
Native OSIS chapter keys (Jonah4, 1Kgs19) - no Chinese mapping involved.
Same filtering as zh pipeline: drop votes<=-10 and intra-chapter self refs.
Emits the SAME globals (__BP/__BP_TOTAL) so page logic is shared verbatim.
"""
import glob, os
from collections import defaultdict

OSIS = [  # (code, chapters) canonical order
    ('Gen',50),('Exod',40),('Lev',27),('Num',36),('Deut',34),('Josh',24),('Judg',21),
    ('Ruth',4),('1Sam',31),('2Sam',24),('1Kgs',22),('2Kgs',25),('1Chr',29),('2Chr',36),
    ('Ezra',10),('Neh',13),('Esth',10),('Job',42),('Ps',150),('Prov',31),('Eccl',12),
    ('Song',8),('Isa',66),('Jer',52),('Lam',5),('Ezek',48),('Dan',12),('Hos',14),
    ('Joel',3),('Amos',9),('Obad',1),('Jonah',4),('Mic',7),('Nah',3),('Hab',3),
    ('Zeph',3),('Hag',2),('Zech',14),('Mal',4),('Matt',28),('Mark',16),('Luke',24),
    ('John',21),('Acts',28),('Rom',16),('1Cor',16),('2Cor',13),('Gal',6),('Eph',6),
    ('Phil',4),('Col',4),('1Thess',5),('2Thess',3),('1Tim',6),('2Tim',4),('Titus',3),
    ('Phlm',1),('Heb',13),('Jas',5),('1Pet',5),('2Pet',3),('1John',5),('2John',1),
    ('3John',1),('Jude',1),('Rev',22),
]
IDX = {code: i for i, (code, _) in enumerate(OSIS)}

def parse_ref(s):
    first = s.split('-')[0]
    book, ch, v = first.rsplit('.', 2)
    return IDX[book], int(ch), int(v)

def range_str(s):
    parts = s.split('-')
    _, c1, v1 = parse_ref(parts[0])
    if len(parts) == 1:
        return str(v1)
    _, c2, v2 = parse_ref(parts[1])
    return f'{v1}-{v2}' if c1 == c2 else str(v1)

HERE = os.path.dirname(os.path.abspath(__file__))
rows = kept = heavy_neg = self_ch = 0
pairs = {}

with open(os.path.join(HERE, 'cross_references.txt'), encoding='utf-8') as f:
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
        if (ia, ca) <= (ib, cb):
            key, ex = (ia, ca, ib, cb), (str(va), range_str(cols[1]))
        else:
            key, ex = (ib, cb, ia, ca), (range_str(cols[1]).split('-')[0], str(va))
        p = pairs.get(key)
        if p is None:
            pairs[key] = [v, 1, v, ex[0], ex[1]]
        else:
            p[0] += v
            p[1] += 1
            if v > p[2]:
                p[2], p[3], p[4] = v, ex[0], ex[1]

out = []
for (ia, ca, ib, cb), (sv, n, mv, exa, exb) in pairs.items():
    out.append([OSIS[ia][0] + str(ca), OSIS[ib][0] + str(cb), sv, n, exa, exb])
out.sort(key=lambda r: -r[2])

lines = ['|'.join([r[0], r[1], str(r[2]), str(r[3]), r[4], r[5]]) for r in out]
LIMIT = int(1.7 * 1024 * 1024)
chunks, cur, size = [], [], 0
for row in lines:
    b = len(row.encode('utf-8')) + 1
    if size + b > LIMIT and cur:
        chunks.append(cur); cur, size = [], 0
    cur.append(row); size += b
if cur:
    chunks.append(cur)

for old in glob.glob(os.path.join(HERE, 'beads-en-*.js')):
    os.remove(old)
K = len(chunks)
for i, chunk in enumerate(chunks, 1):
    path = os.path.join(HERE, f'beads-en-{i}.js')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('// BeadString chapter-level bead shard %d/%d - TSK/OpenBible (CC-BY)\n' % (i, K))
        f.write('// row: chA|chB|votes|records|exA|exB, rows joined by ;\n')
        f.write('window.__BP=(window.__BP||[]);window.__BP.push("')
        f.write(';'.join(chunk))
        f.write('");window.__BP_TOTAL=%d;\n' % K)
    print(f'beads-en-{i}.js {os.path.getsize(path)/1e6:.2f}MB')

print('pairs:', len(pairs), '| dropped heavy-neg:', heavy_neg, '| intra-chapter:', self_ch)
print('Top3:', out[:3])

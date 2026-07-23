# -*- coding: utf-8 -*-
"""v2 节级线索索引：cross_references.txt (34.4万行, 节级) -> data/tsk/<OSIS>.js 按卷分片
每行: fromCh:fromV|toBookCh:verses|votes   （与 pipeline 同滤: votes<=-10 与同章内自引剔除）
另出 data/tsk/zhmap.js：OSIS码 -> 中文缩写（zh 页把 OSIS 索引渲染成中文引用，索引本体单份四语共用）
用法: python threads.py
"""
import os
from collections import defaultdict

OSIS = [
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
IDX = {code: i for i, (code, _, _) in enumerate(OSIS)}

def parse_ref(s):
    first = s.split('-')[0]
    book, ch, v = first.rsplit('.', 2)
    return book, int(ch), int(v)

def to_compact(s):
    """'Exod.34.6-Exod.34.7' -> 'Exod34:6-7'；跨章 range 取起点"""
    parts = s.split('-')
    b1, c1, v1 = parse_ref(parts[0])
    if len(parts) == 1:
        return f'{b1}{c1}:{v1}'
    b2, c2, v2 = parse_ref(parts[1])
    if b1 == b2 and c1 == c2 and v2 > v1:
        return f'{b1}{c1}:{v1}-{v2}'
    return f'{b1}{c1}:{v1}'

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'tsk')
os.makedirs(OUT, exist_ok=True)

rows = kept = 0
books = defaultdict(list)   # code -> [(ch, v, toRef, votes)]

with open(os.path.join(HERE, 'cross_references.txt'), encoding='utf-8') as f:
    next(f)
    for line in f:
        cols = line.rstrip('\n').split('\t')
        if len(cols) < 3:
            continue
        rows += 1
        try:
            votes = int(cols[2])
            fb, fc, fv = parse_ref(cols[0])
            tb, tc, tv = parse_ref(cols[1])
            if fb not in IDX or tb not in IDX:
                continue
        except (ValueError, KeyError):
            continue
        if votes <= -10:
            continue
        if fb == tb and fc == tc:
            continue
        books[fb].append((fc, fv, to_compact(cols[1]), votes))
        kept += 1

total_bytes = 0
for code, _, _ in OSIS:
    lst = sorted(books.get(code, []), key=lambda r: (r[0], r[1], -r[3]))
    body = ';'.join(f'{c}:{v}|{to}|{vt}' for c, v, to, vt in lst)
    js = f"window.TSKX=window.TSKX||{{}};window.TSKX['{code}']='{body}';\n"
    path = os.path.join(OUT, f'{code}.js')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(js)
    total_bytes += len(js.encode('utf-8'))

zhmap = ','.join(f"'{code}':'{zh}'" for code, zh, _ in OSIS)
with open(os.path.join(OUT, 'zhmap.js'), 'w', encoding='utf-8') as f:
    f.write('window.TSK_ZH={' + zhmap + '};\n')

print(f'rows={rows} kept={kept} files=66+zhmap total={total_bytes/1048576:.2f}MB')
biggest = sorted(((len(v), k) for k, v in books.items()), reverse=True)[:5]
print('biggest:', [(k, n) for n, k in biggest])
# 抽查：拿4 <-> 出34 应含 4:2|Exod34:6-7
sample = [r for r in books['Jonah'] if r[0] == 4 and r[2].startswith('Exod34')]
print('Jonah4->Exod34:', sample)

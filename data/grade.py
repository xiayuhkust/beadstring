# -*- coding: utf-8 -*-
"""串珠难度分级 v1 —— 明线/暗线（用户群反馈：同词连接太简单，要分深浅）

原理（见《串珠分级与每日一串.md》）：二维矩阵 = TSK votes × 词汇重叠度。
v1 在 KJV 译文层计算重叠（跨约的线希伯来/希腊 lemma 本就不互通，译文层全经统一；
原文 lemma 层留待后续精化）。打分借 Tesserae 思路：共享词按逆文档频率加权——
共享的词越稀有，关联越显性。

档位（写进 tsk 分片第 4 字段 + beads-grade 珠级字符串）：
  b 明线：共享词得分高——同样的用词，一眼可见
  d 暗线：几乎无共享实词 且 votes>=3——人类认可却无共词，主题/预表层
  （空）平：介于两者之间
用法：python grade.py stats   只看分布与样例（定阈值用）
      python grade.py        产出 grades.tsv + beads-grade.js + beads-grade-en.js
"""
import io, json, math, os, re, sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

OSIS = ['Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam',
        '1Kgs','2Kgs','1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov',
        'Eccl','Song','Isa','Jer','Lam','Ezek','Dan','Hos','Joel','Amos',
        'Obad','Jonah','Mic','Nah','Hab','Zeph','Hag','Zech','Mal',
        'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph',
        'Phil','Col','1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas',
        '1Pet','2Pet','1John','2John','3John','Jude','Rev']
ZH = ['创','出','利','民','申','书','士','得','撒上','撒下','王上','王下','代上','代下','拉',
      '尼','斯','伯','诗','箴','传','歌','赛','耶','哀','结','但','何','珥','摩',
      '俄','拿','弥','鸿','哈','番','该','亚','玛',
      '太','可','路','约','徒','罗','林前','林后','加','弗','腓','西','帖前','帖后','提前',
      '提后','多','门','来','雅','彼前','彼后','约壹','约贰','约叁','犹','启']
IDX = {b: i for i, b in enumerate(OSIS)}
ZH2I = {z: i for i, z in enumerate(ZH)}

# 语法性停用词（KJV 古体在内）；常见实词交给 idf 自然降权
STOP = set('''a an and are as at be but by for from he her him his i in is it its me my
not of on or our she so that the their them they this to was we with you your ye thee
thou thy thine unto hath hast doth dost shalt wilt art all also am any because been
before both came come did do even every go had have if into no nor now o out over said
saith say shall she some then there therefore these things thing those up upon were what
when which who whom will yea his her him again against among behold down forth many more
most much let us made make may men man might mine own same they'''.split())

def stem(w):
    for suf in ('eth', 'est', 'ing', 'ed', 'es', "'s", 's'):
        if len(w) - len(suf) >= 3 and w.endswith(suf):
            return w[:-len(suf)]
    return w

def tokens(text):
    out = set()
    for w in re.findall(r"[a-z']+", text.lower().replace('{', ' ').replace('}', ' ')):
        w = w.strip("'")
        if len(w) < 2 or w in STOP:
            continue
        out.add(stem(w))
    return out

# ---- KJV 库 ----
kjv = json.load(io.open(os.path.join(HERE, 'kjv.json'), encoding='utf-8-sig'))
assert len(kjv) == 66
VT = {}   # (bookIdx, ch, v) -> token set
DF = defaultdict(int)
for bi, book in enumerate(kjv):
    for ci, chap in enumerate(book['chapters'], 1):
        for vi, text in enumerate(chap, 1):
            t = tokens(text)
            VT[(bi, ci, vi)] = t
            for w in t:
                DF[w] += 1
N = len(VT)
def idf(w): return math.log10(N / DF[w])

def parse_ref(s):
    p = s.split('.')
    return IDX[p[0]], int(p[1]), int(p[2])

def range_tokens(ref):
    """'Ps.148.4-Ps.148.5' → 范围（≤5 节）token 并集；返回 (tokens, 首节三元组)"""
    parts = ref.split('-')
    b, c, v = parse_ref(parts[0])
    hi = v
    if len(parts) == 2:
        b2, c2, v2 = parse_ref(parts[1])
        if b2 == b and c2 == c and v2 > v:
            hi = min(v2, v + 4)
    out = set()
    for x in range(v, hi + 1):
        out |= VT.get((b, c, x), set())
    return out, (b, c, v)

def score_pair(fromRef, toRef):
    fb, fc, fv = parse_ref(fromRef)
    ta = VT.get((fb, fc, fv), set())
    tb, _ = range_tokens(toRef)
    return sum(idf(w) for w in ta & tb)

# ---- 全量打分 ----
rows = []
with io.open(os.path.join(HERE, 'cross_references.txt'), encoding='utf-8') as f:
    next(f)
    for line in f:
        cols = line.rstrip('\n').split('\t')
        if len(cols) < 3:
            continue
        try:
            votes = int(cols[2])
            fb, fc, fv = parse_ref(cols[0])
            tb0, tc0, tv0 = parse_ref(cols[1].split('-')[0])
        except (ValueError, KeyError, IndexError):
            continue
        if votes <= -10 or (fb == tb0 and fc == tc0):
            continue
        try:
            sc = score_pair(cols[0], cols[1])
        except KeyError:
            continue
        rows.append((cols[0], cols[1], votes, sc))

BRIGHT, DEEP = 4.0, 1.5   # 明线：≥两个中频独特词或一个罕词；暗线：连一个像样的实词都不共享

def grade(votes, sc):
    if sc >= BRIGHT: return 'b'
    if sc <= DEEP and votes >= 3: return 'd'
    return ''

if len(sys.argv) > 1 and sys.argv[1] == 'stats':
    ss = sorted(r[3] for r in rows)
    def pct(p): return ss[int(len(ss) * p / 100)]
    print('threads=%d  score pct: p10=%.2f p25=%.2f p50=%.2f p60=%.2f p75=%.2f p90=%.2f'
          % (len(rows), pct(10), pct(25), pct(50), pct(60), pct(75), pct(90)))
    from collections import Counter
    c = Counter(grade(v, s) for _, _, v, s in rows)
    print('grades:', dict(c))
    import random
    random.seed(7)
    for label, cond in [('BRIGHT', lambda v, s: s >= BRIGHT),
                        ('DEEP', lambda v, s: s <= DEEP and v >= 3),
                        ('MID', lambda v, s: DEEP < s < BRIGHT)]:
        pool = [r for r in rows if cond(r[2], r[3])]
        print('\n--', label, len(pool))
        for r in random.sample(pool, min(5, len(pool))):
            print('  %.1f v=%d  %s -> %s' % (r[3], r[2], r[0], r[1]))
    sys.exit()

# ---- 产出 1：grades.tsv（threads.py 消费）----
n_b = n_d = 0
with io.open(os.path.join(HERE, 'grades.tsv'), 'w', encoding='utf-8') as f:
    for fr, to, votes, sc in rows:
        g = grade(votes, sc)
        if g:
            f.write('%s\t%s\t%s\n' % (fr, to, g))
            if g == 'b': n_b += 1
            else: n_d += 1
print('grades.tsv: bright=%d deep=%d mid=%d' % (n_b, n_d, len(rows) - n_b - n_d))

# ---- 产出 2：珠级档位（按 beads 文件行序，代表线 = r[4]/r[5] 节对）----
GK = {}
for fr, to, votes, sc in rows:
    g = grade(votes, sc) or 'p'
    fb, fc, fv = parse_ref(fr)
    tb, tc, tv = parse_ref(to.split('-')[0])
    GK[(fb, fc, fv, tb, tc, tv)] = g
    GK[(tb, tc, tv, fb, fc, fv)] = g

CH = re.compile(r'^([1-3]?[A-Za-z]+|[^0-9]+)(\d+)$')
def bead_grades(files, zh):
    chars = []
    for fn in files:
        s = io.open(os.path.join(HERE, fn), encoding='utf-8').read()
        m = re.search(r'push\("(.+?)"\);window', s, re.S)
        for row in m.group(1).split(';'):
            p = row.split('|')
            ma, mb = CH.match(p[0]), CH.match(p[1])
            bi_a = ZH2I.get(ma.group(1)) if zh else IDX.get(ma.group(1))
            bi_b = ZH2I.get(mb.group(1)) if zh else IDX.get(mb.group(1))
            va = int(re.match(r'(\d+)', p[4]).group(1))
            vb = int(re.match(r'(\d+)', p[5]).group(1))
            key = (bi_a, int(ma.group(2)), va, bi_b, int(mb.group(2)), vb)
            chars.append(GK.get(key, 'p'))
    return ''.join(chars)

for out, files, zh in [('beads-grade.js', ['beads-1.js', 'beads-2.js'], True),
                       ('beads-grade-en.js', ['beads-en-1.js', 'beads-en-2.js'], False)]:
    g = bead_grades(files, zh)
    io.open(os.path.join(HERE, out), 'w', encoding='utf-8').write(
        '// 珠级档位（b 明线/d 暗线/p 平），下标对齐 BEADS 行序 · 自动编目非权威\n'
        "window.BGRADE='%s';\n" % g)
    from collections import Counter
    print(out, len(g), dict(Counter(g)))

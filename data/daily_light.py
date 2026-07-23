# -*- coding: utf-8 -*-
"""Daily Light on the Daily Path（Bagster 1875，公版）→ data/daily-light.js

来源：CCEL 单日页（scratchpad/dl_html/dMMDD{am|pm}.html，fetch_dl.py 抓取）。
页面里每个 <a class="scripRef"> 带 name="_Book_c1_v1_c2_v2"（规范化引用）：
  第一个 scripRef = 领句出处；font-size:x-small span 里的 = 链上各节（按序）。
校验：引用必须存在于 kjv.json（书/章/节界内）；越界/未知书卷记录到 stderr 人工处理。
输出：window.DLIGHT = {'0101am': 'Phil3:13-14|John17:24;2Tim1:12;...', ...}
（仅引用不含经文——客户端从 verses 库取文，中文=同节和合本，铁则内。）
"""
import io, json, os, re, sys, calendar

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.environ.get('DL_SRC', ''), '') or os.path.join(
    r'C:\Users\Administrator\AppData\Local\Temp\claude\E----',
    r'35c932c5-d4e0-4c1f-940d-48b0cc6f2bde', 'scratchpad', 'dl_html')

OSIS = ['Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam',
        '1Kgs','2Kgs','1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov',
        'Eccl','Song','Isa','Jer','Lam','Ezek','Dan','Hos','Joel','Amos',
        'Obad','Jonah','Mic','Nah','Hab','Zeph','Hag','Zech','Mal',
        'Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal','Eph',
        'Phil','Col','1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas',
        '1Pet','2Pet','1John','2John','3John','Jude','Rev']
IDX = {b: i for i, b in enumerate(OSIS)}
# CCEL name 属性偶见的别名
ALIAS = {'Psa': 'Ps', 'Sol': 'Song', 'SS': 'Song', 'Rev22': 'Rev'}

kjv = json.load(io.open(os.path.join(HERE, 'kjv.json'), encoding='utf-8-sig'))

def vcount(b, c):
    try: return len(kjv[IDX[b]]['chapters'][c - 1])
    except (KeyError, IndexError): return 0

REF = re.compile(r'name="_([1-3]?[A-Za-z]+)_(\d+)_(\d+)_(\d+)_(\d+)"')

def norm(m, where, fn, problems):
    b = ALIAS.get(m[0], m[0])
    c1, v1, c2, v2 = int(m[1]), int(m[2]), int(m[3]), int(m[4])
    if b not in IDX:
        problems.append('%s %s: unknown book %s' % (fn, where, m[0])); return None
    n = vcount(b, c1)
    if not (1 <= v1 <= n):
        problems.append('%s %s: %s %d:%d out of range (max %d)' % (fn, where, b, c1, v1, n))
        return None
    if c2 == c1 and v2 > v1 and v2 <= n:
        return '%s%d:%d-%d' % (b, c1, v1, v2)
    return '%s%d:%d' % (b, c1, v1)

def toks(t):
    return set(w for w in re.findall(r"[a-z']+", t.lower()) if len(w) >= 4)

def verse_toks(b, c, v1, v2):
    out = set()
    for v in range(v1, v2 + 1):
        try: out |= toks(kjv[IDX[b]]['chapters'][c - 1][v - 1])
        except IndexError: pass
    return out

def text_check(ref, body_toks, fn, problems):
    """经文文字反查：该引用的经文词是否真出现在页面正文里；
    不在 → 在同章:节的其他书卷里找最像的（治 CCEL 的 Matt/Mark 式排印错）"""
    m = re.match(r'^([1-3]?[A-Za-z]+)(\d+):(\d+)(?:-(\d+))?$', ref)
    b, c, v1 = m.group(1), int(m.group(2)), int(m.group(3))
    v2 = int(m.group(4) or v1)
    mine = verse_toks(b, c, v1, v2)
    if not mine:
        return ref
    score = len(mine & body_toks) / len(mine)
    if score >= 0.35:
        return ref
    best, bs = None, 0.0
    for alt in OSIS:
        if alt == b or not (1 <= v2 <= vcount(alt, c)):
            continue
        at = verse_toks(alt, c, v1, v2)
        if not at: continue
        asc = len(at & body_toks) / len(at)
        if asc > bs: best, bs = alt, asc
    if best and bs >= 0.85 and bs > score + 0.3:
        fixed = '%s%d:%d' % (best, c, v1) + ('-%d' % v2 if v2 > v1 else '')
        problems.append('%s: FIXED misprint %s -> %s (%.2f vs %.2f)' % (fn, ref, fixed, bs, score))
        return fixed
    problems.append('%s: SUSPECT %s (%.2f in-page match, no better candidate)' % (fn, ref, score))
    return ref

def parse_page(fn, problems):
    s = io.open(os.path.join(SRC, fn), encoding='utf-8', errors='replace').read()
    i = s.find('book-content')
    j = s.find('book_navbar_bottom')
    body = s[i:j if j > i else len(s)]
    body_toks = toks(re.sub(r'<[^>]+>', ' ', body))
    # 链上各节：x-small span 里的引用
    chain = []
    for span in re.findall(r'font-size:x-small.*?</span>', body, re.S):
        chain += [norm(m, 'chain', fn, problems) for m in REF.findall(span)]
    chain = [text_check(c, body_toks, fn, problems) for c in chain if c]
    # 领句：正文里第一个引用
    lead_m = REF.search(body)
    lead = norm(lead_m.groups(), 'lead', fn, problems) if lead_m else None
    if not lead or not chain:
        problems.append('%s: lead=%s chain=%d' % (fn, lead, len(chain)))
        return None
    # 领句若混进链（个别页首条即领句重复），不去重——原书顺序即作品
    return lead + '|' + ';'.join(chain)

entries, problems, missing = {}, [], []
for mo in range(1, 13):
    for d in range(1, calendar.monthrange(2024, mo)[1] + 1):
        for ap in ('am', 'pm'):
            fn = 'd%02d%02d%s.html' % (mo, d, ap)
            if not os.path.exists(os.path.join(SRC, fn)):
                missing.append(fn); continue
            r = parse_page(fn, problems)
            if r:
                entries['%02d%02d%s' % (mo, d, ap)] = r

out = os.path.join(HERE, 'daily-light.js')
body = ','.join("'%s':'%s'" % (k, v) for k, v in sorted(entries.items()))
io.open(out, 'w', encoding='utf-8').write(
    '// Daily Light on the Daily Path (Bagster ~1875, public domain) · refs only\n'
    '// source: CCEL transcription; misprint-checked against KJV verse bounds\n'
    'window.DLIGHT={' + body + '};\n')

print('entries=%d missing=%d problems=%d size=%.1fKB'
      % (len(entries), len(missing), len(problems), os.path.getsize(out) / 1024))
for p in problems:
    sys.stderr.write(p + '\n')
if missing[:3]:
    print('first missing:', missing[:3])

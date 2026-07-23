# -*- coding: utf-8 -*-
# BeadString multi-language verse pipeline
# getBible v2 JSON -> verses-<lang>-N.js (native OSIS keys, same globals as en) + books-<lang>.js
# usage: python verses_lang.py es | python verses_lang.py pt
import json, io, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

OSIS = ['Gen','Exod','Lev','Num','Deut','Josh','Judg','Ruth','1Sam','2Sam','1Kgs','2Kgs',
        '1Chr','2Chr','Ezra','Neh','Esth','Job','Ps','Prov','Eccl','Song','Isa','Jer',
        'Lam','Ezek','Dan','Hos','Joel','Amos','Obad','Jonah','Mic','Nah','Hab','Zeph',
        'Hag','Zech','Mal','Matt','Mark','Luke','John','Acts','Rom','1Cor','2Cor','Gal',
        'Eph','Phil','Col','1Thess','2Thess','1Tim','2Tim','Titus','Phlm','Heb','Jas',
        '1Pet','2Pet','1John','2John','3John','Jude','Rev']

LANGS = {
  'es': {
    'src': 'rv1909.json',
    'full': ['Génesis','Éxodo','Levítico','Números','Deuteronomio','Josué','Jueces','Rut',
      '1 Samuel','2 Samuel','1 Reyes','2 Reyes','1 Crónicas','2 Crónicas','Esdras','Nehemías',
      'Ester','Job','Salmos','Proverbios','Eclesiastés','Cantares','Isaías','Jeremías',
      'Lamentaciones','Ezequiel','Daniel','Oseas','Joel','Amós','Abdías','Jonás','Miqueas',
      'Nahúm','Habacuc','Sofonías','Hageo','Zacarías','Malaquías','Mateo','Marcos','Lucas',
      'Juan','Hechos','Romanos','1 Corintios','2 Corintios','Gálatas','Efesios','Filipenses',
      'Colosenses','1 Tesalonicenses','2 Tesalonicenses','1 Timoteo','2 Timoteo','Tito',
      'Filemón','Hebreos','Santiago','1 Pedro','2 Pedro','1 Juan','2 Juan','3 Juan','Judas',
      'Apocalipsis'],
    'short': ['Gn','Éx','Lv','Nm','Dt','Jos','Jue','Rut','1S','2S','1R','2R','1Cr','2Cr',
      'Esd','Neh','Est','Job','Sal','Pr','Ec','Cnt','Is','Jer','Lm','Ez','Dn','Os','Jl',
      'Am','Abd','Jon','Miq','Nah','Hab','Sof','Hag','Zac','Mal','Mt','Mr','Lc','Jn','Hch',
      'Ro','1Co','2Co','Gá','Ef','Fil','Col','1Ts','2Ts','1Ti','2Ti','Tit','Flm','He','Stg',
      '1P','2P','1Jn','2Jn','3Jn','Jud','Ap'],
    'checks': [('Gen1:1','principio'), ('Jonah4:2','clemente'), ('Ps23:1','pastor'),
               ('John3:16','unigénito'), ('Rev22:21','gracia')],
  },
  'pt': {
    'src': 'blivre.json',
    'full': ['Gênesis','Êxodo','Levítico','Números','Deuteronômio','Josué','Juízes','Rute',
      '1 Samuel','2 Samuel','1 Reis','2 Reis','1 Crônicas','2 Crônicas','Esdras','Neemias',
      'Ester','Jó','Salmos','Provérbios','Eclesiastes','Cantares','Isaías','Jeremias',
      'Lamentações','Ezequiel','Daniel','Oseias','Joel','Amós','Obadias','Jonas','Miqueias',
      'Naum','Habacuque','Sofonias','Ageu','Zacarias','Malaquias','Mateus','Marcos','Lucas',
      'João','Atos','Romanos','1 Coríntios','2 Coríntios','Gálatas','Efésios','Filipenses',
      'Colossenses','1 Tessalonicenses','2 Tessalonicenses','1 Timóteo','2 Timóteo','Tito',
      'Filemom','Hebreus','Tiago','1 Pedro','2 Pedro','1 João','2 João','3 João','Judas',
      'Apocalipse'],
    'short': ['Gn','Êx','Lv','Nm','Dt','Js','Jz','Rt','1Sm','2Sm','1Rs','2Rs','1Cr','2Cr',
      'Ed','Ne','Et','Jó','Sl','Pv','Ec','Ct','Is','Jr','Lm','Ez','Dn','Os','Jl','Am','Ob',
      'Jn','Mq','Na','Hc','Sf','Ag','Zc','Ml','Mt','Mc','Lc','Jo','At','Rm','1Co','2Co',
      'Gl','Ef','Fp','Cl','1Ts','2Ts','1Tm','2Tm','Tt','Fm','Hb','Tg','1Pe','2Pe','1Jo',
      '2Jo','3Jo','Jd','Ap'],
    'checks': [('Gen1:1','princípio'), ('Jonah4:2','misericordioso'), ('Ps23:1','pastor'),
               ('John3:16','unigênito'), ('Rev22:21','graça')],
  },
}

def main(lang):
    cfg = LANGS[lang]
    with io.open(os.path.join(HERE, cfg['src']), encoding='utf-8') as f:
        data = json.load(f)
    books = data['books']
    assert len(books) == 66, len(books)

    entries = []
    for bi, book in enumerate(books):
        code = OSIS[bi]
        for ch in book['chapters']:
            cn = ch['chapter']
            for v in ch['verses']:
                t = ' '.join(str(v['text']).split())
                if t:
                    entries.append((f'{code}{cn}:{v["verse"]}', t))
    print(lang, 'verses:', len(entries))

    LIMIT = 1_700_000
    shards, cur, size = [], [], 0
    for k, t in entries:
        piece = len(k.encode('utf-8')) + len(t.encode('utf-8')) + 8
        if size + piece > LIMIT and cur:
            shards.append(cur); cur, size = [], 0
        cur.append((k, t)); size += piece
    if cur: shards.append(cur)

    for i, shard in enumerate(shards):
        obj = {k: t for k, t in shard}
        body = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
        js = (f'window.VERSES=Object.assign(window.VERSES||{{}},{body});'
              f'window.__VP=(window.__VP||0)+1;window.__VP_TOTAL={len(shards)};')
        path = os.path.join(HERE, f'verses-{lang}-{i+1}.js')
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(js)
        print(f'verses-{lang}-{i+1}.js', f'{os.path.getsize(path)/1e6:.2f}MB', len(obj))

    full = dict(zip(OSIS, cfg['full']))
    short = dict(zip(OSIS, cfg['short']))
    js = ('window.BOOKFULL=' + json.dumps(full, ensure_ascii=False, separators=(',', ':')) +
          ';window.BOOKSHORT=' + json.dumps(short, ensure_ascii=False, separators=(',', ':')) + ';')
    with io.open(os.path.join(HERE, f'books-{lang}.js'), 'w', encoding='utf-8') as f:
        f.write(js)
    print(f'books-{lang}.js written, shards={len(shards)}')

    check = dict(entries)
    for key, frag in cfg['checks']:
        ok = key in check and frag.lower() in check[key].lower()
        print(('OK ' if ok else 'FAIL '), key, '->', check.get(key, 'MISSING')[:70])
    return len(shards)

if __name__ == '__main__':
    for lang in (sys.argv[1:] or ['es', 'pt']):
        main(lang)

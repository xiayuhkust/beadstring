# BeadString native KJV pipeline
# kjv.json -> verses-en-N.js with NATIVE OSIS keys (Jonah4:2) + books-en.js
# Emits the SAME globals as the zh shards (VERSES/__VP/__VP_TOTAL) so page
# logic is shared verbatim; an English page simply loads the -en files.
import json, io, os

HERE = os.path.dirname(os.path.abspath(__file__))

# canonical order: (osis, full English name)
BOOKS = [
    ('Gen','Genesis'),('Exod','Exodus'),('Lev','Leviticus'),('Num','Numbers'),
    ('Deut','Deuteronomy'),('Josh','Joshua'),('Judg','Judges'),('Ruth','Ruth'),
    ('1Sam','1 Samuel'),('2Sam','2 Samuel'),('1Kgs','1 Kings'),('2Kgs','2 Kings'),
    ('1Chr','1 Chronicles'),('2Chr','2 Chronicles'),('Ezra','Ezra'),('Neh','Nehemiah'),
    ('Esth','Esther'),('Job','Job'),('Ps','Psalms'),('Prov','Proverbs'),
    ('Eccl','Ecclesiastes'),('Song','Song of Solomon'),('Isa','Isaiah'),('Jer','Jeremiah'),
    ('Lam','Lamentations'),('Ezek','Ezekiel'),('Dan','Daniel'),('Hos','Hosea'),
    ('Joel','Joel'),('Amos','Amos'),('Obad','Obadiah'),('Jonah','Jonah'),
    ('Mic','Micah'),('Nah','Nahum'),('Hab','Habakkuk'),('Zeph','Zephaniah'),
    ('Hag','Haggai'),('Zech','Zechariah'),('Mal','Malachi'),('Matt','Matthew'),
    ('Mark','Mark'),('Luke','Luke'),('John','John'),('Acts','Acts'),('Rom','Romans'),
    ('1Cor','1 Corinthians'),('2Cor','2 Corinthians'),('Gal','Galatians'),
    ('Eph','Ephesians'),('Phil','Philippians'),('Col','Colossians'),
    ('1Thess','1 Thessalonians'),('2Thess','2 Thessalonians'),('1Tim','1 Timothy'),
    ('2Tim','2 Timothy'),('Titus','Titus'),('Phlm','Philemon'),('Heb','Hebrews'),
    ('Jas','James'),('1Pet','1 Peter'),('2Pet','2 Peter'),('1John','1 John'),
    ('2John','2 John'),('3John','3 John'),('Jude','Jude'),('Rev','Revelation'),
]

def main():
    with io.open(os.path.join(HERE, 'kjv.json'), encoding='utf-8-sig') as f:
        kjv = json.load(f)
    assert len(kjv) == 66, len(kjv)

    entries = []
    for bi, book in enumerate(kjv):
        code = BOOKS[bi][0]
        for ci, chapter in enumerate(book['chapters']):
            for vi, text in enumerate(chapter):
                # {} marks KJV supplied (italic) words - drop braces, keep words
                t = text.replace('\\', '').replace('{', '').replace('}', '').strip()
                t = ' '.join(t.split())
                entries.append((f'{code}{ci+1}:{vi+1}', t))
    print('verses:', len(entries))

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
        path = os.path.join(HERE, f'verses-en-{i+1}.js')
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(js)
        print(f'verses-en-{i+1}.js', f'{os.path.getsize(path)/1e6:.2f}MB', len(obj), 'verses')

    full = {code: name for code, name in BOOKS}
    js = 'window.BOOKFULL=' + json.dumps(full, separators=(',', ':')) + ';'
    with io.open(os.path.join(HERE, 'books-en.js'), 'w', encoding='utf-8') as f:
        f.write(js)
    print('books-en.js written')

    check = dict(entries)
    for key, frag in [('Gen1:1', 'In the beginning'), ('Jonah4:2', 'gracious God'),
                      ('Exod34:6', 'merciful and gracious'), ('Ps23:1', 'my shepherd'),
                      ('John3:16', 'only begotten Son'), ('Rev22:21', 'grace of our Lord')]:
        ok = key in check and frag.lower() in check[key].lower()
        print(('OK ' if ok else 'FAIL '), key, '->', check.get(key, 'MISSING')[:60])

if __name__ == '__main__':
    main()

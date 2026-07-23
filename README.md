# BeadString · 串珠

**Handcraft of the Wilderness — read both ends of a bead, find the thread, tie your own knot.**

Live: **https://beadstring.app** (English default · 中文 / Español / Português)

BeadString is a non-profit devotional web app built on the ~340,000 cross-references
of the *Treasury of Scripture Knowledge* (via OpenBible.info). A "bead" joins two
scripture passages; you read both ends, mark the words you believe are joined,
and write down why. Finished strands are kept in your workshop.

三大铁则 / three house rules:

1. **No quizzes, no right answers.** Users may swap a bead or reveal the marked words at any time.
2. **The platform never authors interpretation.** Only verifiable things are on the
   table: scripture text, TSK cross-reference facts, and readers' own notes
   (clearly marked as non-authoritative). The TSK dataset is never edited —
   community contributions live beside it, never inside it.
3. **Machine translation is used only for UI and interface text** — never for
   scripture or interpretation.

## Open source & open data

- **Code** — MIT (see LICENSE).
- **Community dataset** — `data/community/community-strands.json`: the notes users
  explicitly chose to publish, exported periodically. **CC BY-SA 4.0.**
  No user identifiers of any kind are included (no e-mails, ids, or names).
  The in-app publish checkbox states that public notes join this dataset.
- Private strands, accounts and anything not explicitly published never leave
  the database.

## Data sources & licenses

| Data | Source | License |
|---|---|---|
| Cross references (~340k) | [OpenBible.info](https://www.openbible.info/labs/cross-references/) (based on the public-domain TSK) | CC BY |
| KJV text | public domain | PD |
| 和合本 (Chinese Union Version) | public domain | PD |
| Reina-Valera 1909 (es) | public domain | PD |
| Bíblia Livre (pt) | [getBible](https://getbible.net/) | CC BY 3.0 BR |
| Community strands | this repo, `data/community/` | CC BY-SA 4.0 |

## Repository layout

```
chuanzhu/            the app (static, no build step) — zh pages at root, en/ + generated es/ pt/
  make_lang_pages.py generates es/pt pages from the en pages (translation tables inside)
  account.js         cloud account & sync (Supabase, magic-code sign-in, RLS)
  sw.js              service worker: content-hash cache-first data, network-first pages
data/                pipelines + generated shards
  pipeline.py / pipeline_en.py     TSK -> chapter-level bead library (zh keys / OSIS keys)
  verses*.py                        bible text -> verse shards per language
  threads.py                        TSK -> verse-level thread index, 66 per-book shards
  export_community.py               community open-data export (needs admin token, not in repo)
  community/                        published open dataset (CC BY-SA 4.0)
社区版建表.sql        Supabase schema: profiles / strands / states / amens + RLS + bead_notes()
deploy.ps1           build dist-cf and deploy to Cloudflare Pages (reads untracked cloudflare.txt)
```

The app is plain HTML/CSS/JS — open `chuanzhu/index.html` from a local server and
it runs (cloud features activate only on beadstring.app).

## Credits

Cross-reference data: Treasury of Scripture Knowledge, votes and curation by
[OpenBible.info](https://www.openbible.info/) (CC BY).

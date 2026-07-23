# -*- coding: utf-8 -*-
"""BeadString 开放数据导出：公开的社区串档 → data/community/community-strands.json
只导出用户明确勾选公开的理由；不含任何用户标识（无邮箱、无 id、无署名）。
数据许可：CC BY-SA 4.0。定期运行并提交到仓库即为一次数据发布。
用法: python export_community.py   （需 supbase.txt 第 4 行的管理 API 令牌，该文件不入库）
"""
import io, json, os, urllib.request
from datetime import date, timezone, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

with io.open(os.path.join(ROOT, 'supbase.txt'), encoding='utf-8') as f:
    lines = [x.strip() for x in f if x.strip()]
TOKEN = next(x for x in lines if x.startswith('sbp_'))

SQL = """
select s.pair_key, s.refs, s.reason, s.lang, s.strung_on,
       (select count(*) from amens a where a.strand_id = s.id)::int as amens
from strands s
where s.is_public and s.reason <> ''
order by s.pair_key, s.strung_on
"""

req = urllib.request.Request(
    'https://api.supabase.com/v1/projects/cecnssdqysxaofkywhkg/database/query',
    data=json.dumps({'query': SQL}).encode('utf-8'),
    headers={'Authorization': 'Bearer ' + TOKEN, 'Content-Type': 'application/json',
             'User-Agent': 'beadstring-export/1.0'},
    method='POST')
rows = json.loads(urllib.request.urlopen(req, timeout=60).read().decode('utf-8'))

out = {
    'dataset': 'BeadString community strands (public notes)',
    'homepage': 'https://beadstring.app',
    'source': 'https://github.com/xiayuhkust/beadstring',
    'license': 'CC BY-SA 4.0',
    'note': ('User-contributed reasons on TSK cross-reference bead pairs. '
             'Only notes the author explicitly chose to publish. '
             'No user identifiers included. '
             'pair_key uses OSIS chapter codes for en/es/pt and Chinese Union Version '
             'abbreviations for zh.'),
    'exported_on': datetime.now(timezone.utc).strftime('%Y-%m-%d'),
    'count': len(rows),
    'strands': rows,
}

outdir = os.path.join(HERE, 'community')
os.makedirs(outdir, exist_ok=True)
path = os.path.join(outdir, 'community-strands.json')
with io.open(path, 'w', encoding='utf-8') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('exported', len(rows), 'strands ->', path)

# BeadString · 部署（海外唯一入口：Cloudflare Pages / beadstring.app）
# 用法: powershell -File deploy.ps1
# 布局：根 = 英文；/zh /en /es /pt 各语言全量子目录
# 注：CloudBase 国内镜像已停止维护（2026-07-22 用户决定），旧内容保留在线不再更新
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$src  = Join-Path $root 'chuanzhu'
$v    = Get-Date -Format 'yyyyMMddHHmm'

$assets = @('tokens.css', 'theme-huiben.css', 'account.js', 'sw.js',
            'icon-192.png', 'icon-512.png', 'icon-180.png')
$pages  = @('index.html', 'shujia.html', 'gongfang.html', 'dushu.html')
$langs = @{
  'zh' = @($src, 'manifest.json')
  'en' = @((Join-Path $src 'en'), 'manifest-en.json')
  'es' = @((Join-Path $src 'es'), 'manifest-es.json')
  'pt' = @((Join-Path $src 'pt'), 'manifest-pt.json')
}

# 数据文件用内容哈希做缓存戳：数据不变则 URL 不变，部署不再作废用户已缓存的 7MB 经文
# （小的皮肤/账户文件仍用构建时间戳，改动即刷新）
$script:dataHash = @{}
function Stamp-Html($dir) {
  $ev = [System.Text.RegularExpressions.MatchEvaluator]{
    param($m)
    $name = $m.Groups[1].Value
    $h8 = $script:dataHash[$name]
    if ($h8) { 'data/' + $name + '?v=' + $h8 } else { $m.Value }
  }
  foreach ($h in Get-ChildItem $dir -Filter *.html) {
    $c = [System.IO.File]::ReadAllText($h.FullName, [System.Text.Encoding]::UTF8)
    $c = [regex]::Replace($c, 'data/((?:beads|verses|books)[A-Za-z\-\d]*\.js)', $ev)
    $c = $c -replace '(tokens\.css|theme-huiben\.css|account\.js)', ('$1?v=' + $v)
    [System.IO.File]::WriteAllText($h.FullName, $c, (New-Object System.Text.UTF8Encoding($false)))
  }
}
function Rewrite-DataPath($dir) {
  foreach ($h in Get-ChildItem $dir -Filter *.html) {
    $c = [System.IO.File]::ReadAllText($h.FullName, [System.Text.Encoding]::UTF8)
    $c = $c -replace '\.\./data/', 'data/'
    [System.IO.File]::WriteAllText($h.FullName, $c, (New-Object System.Text.UTF8Encoding($false)))
  }
}
function Copy-LangPages($fromDir, $manifest, $toDir) {
  foreach ($p in $pages) { Copy-Item (Join-Path $fromDir $p) $toDir }
  Copy-Item (Join-Path $fromDir $manifest) $toDir
  foreach ($a in $assets) { Copy-Item (Join-Path $src $a) $toDir }
}

# 1. 构建
$dist = Join-Path $root 'dist-cf'
if (Test-Path $dist) { Remove-Item -Recurse -Force $dist }
New-Item -ItemType Directory -Force (Join-Path $dist 'data') | Out-Null
Copy-Item (Join-Path $root 'data\beads-*.js')  (Join-Path $dist 'data')
Copy-Item (Join-Path $root 'data\verses-*.js') (Join-Path $dist 'data')
Copy-Item (Join-Path $root 'data\books*.js')   (Join-Path $dist 'data')
# v2 节级线索索引（TSK 不可变，无需 ?v 戳）
New-Item -ItemType Directory -Force (Join-Path $dist 'data\tsk') | Out-Null
Copy-Item (Join-Path $root 'data\tsk\*.js') (Join-Path $dist 'data\tsk')
foreach ($f in Get-ChildItem (Join-Path $dist 'data') -Filter *.js) {
  $script:dataHash[$f.Name] = (Get-FileHash $f.FullName -Algorithm MD5).Hash.Substring(0, 8).ToLower()
}
foreach ($l in $langs.Keys) {
  $sub = Join-Path $dist $l
  New-Item -ItemType Directory -Force $sub | Out-Null
  Copy-LangPages $langs[$l][0] $langs[$l][1] $sub
  Stamp-Html $sub
}
Copy-LangPages $langs['en'][0] $langs['en'][1] $dist
Rewrite-DataPath $dist
Stamp-Html $dist
Write-Host "built dist-cf (en@root, langs zh en es pt), v=$v"

# 2. 部署 Cloudflare Pages
$cfFile = Join-Path $root 'cloudflare.txt'
if (-not (Test-Path $cfFile)) { throw 'cloudflare.txt not found' }
$cfLines = Get-Content $cfFile
$env:CLOUDFLARE_API_TOKEN = $cfLines[0].Trim()
$m = ($cfLines -join ' ') | Select-String -Pattern '([0-9a-f]{32})'
$env:CLOUDFLARE_ACCOUNT_ID = $m.Matches[0].Groups[1].Value
wrangler pages deploy $dist --project-name=beadstring --branch=main --commit-dirty=true

Write-Host ""
Write-Host "https://beadstring.app  EN@root · /zh /es /pt"

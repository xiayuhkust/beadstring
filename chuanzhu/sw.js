// BeadString Service Worker · 真缓存版（2026-07-23）
// 策略：
//  - 数据/资产（同源静态文件，URL 带内容哈希或时间戳，唯一即不变）：缓存优先——
//    经文/珠库/线索引下载一次永久可用，弱网与离线照常打开
//  - 页面 HTML：网络优先，失败落缓存——更新即时可达，断网可离线
//  - 跨域（supabase / jsdelivr）不缓存，走网络
const ASSETS = 'bs-assets-v1';
const PAGES = 'bs-pages-v1';

self.addEventListener('install', () => self.skipWaiting());
self.addEventListener('activate', (e) => {
  e.waitUntil((async () => {
    // 清掉未来可能废弃的旧版缓存桶
    for (const k of await caches.keys()) {
      if (k !== ASSETS && k !== PAGES) await caches.delete(k);
    }
    await self.clients.claim();
  })());
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  const isPage = req.mode === 'navigate' || /\.html$/.test(url.pathname) ||
    url.pathname.endsWith('/');

  if (isPage) {
    e.respondWith((async () => {
      try {
        const r = await fetch(req);
        if (r.ok) (await caches.open(PAGES)).put(req, r.clone());
        return r;
      } catch (err) {
        const hit = await caches.match(req, { ignoreSearch: true });
        if (hit) return hit;
        throw err;
      }
    })());
    return;
  }

  e.respondWith((async () => {
    const hit = await caches.match(req);
    if (hit) return hit;
    const r = await fetch(req);
    if (r.ok) {
      const cache = await caches.open(ASSETS);
      // 同路径旧戳条目清理（?v= 换代时不积垃圾）
      for (const k of await cache.keys()) {
        if (new URL(k.url).pathname === url.pathname) await cache.delete(k);
      }
      await cache.put(req, r.clone());
    }
    return r;
  })());
});

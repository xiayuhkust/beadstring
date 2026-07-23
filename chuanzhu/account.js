// BeadString · 云端账户与同步（P2a）
// 常规登录形态：右上角用户图标（全页面）+ 下拉面板；工坊未登录时进门横幅提醒
// 仅在海外站激活；四语文案内置；supabase-js 按需加载（有会话/回跳/点开面板才加载）
// anon key 设计上可公开，数据安全由行级安全策略(RLS)保证
(function () {
  if (!/(^|\.)beadstring\.app$|\.pages\.dev$|^localhost$/.test(location.hostname)) return;

  const SUPA_URL = 'https://cecnssdqysxaofkywhkg.supabase.co';
  const SUPA_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNlY25zc2RxeXN4YW9ma3l3aGtnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ2ODc0NTksImV4cCI6MjEwMDI2MzQ1OX0.zfll9rpAsgukN4j5zb7LX69E3TsVL7Hz7FKkr5WqCzk';
  const LANG = (document.documentElement.lang || 'en').slice(0, 2);

  const DICT = {
    zh: { title: '云 端 存 档', intro: '登录后，你的串珠、串珠历、读经位置在任何设备上都跟着你。本机始终留有一份。',
      email: '输入邮箱', send: '发 登 录 码', sending: '发送中…',
      sent: '邮件已发出——把里面的 6 位登录码输在下面（或在本设备点开邮件里的链接）。',
      code: '6 位登录码', verify: '登 录', verifying: '验证中…',
      codeErr: '码不对或已过期——检查一下，或重新发一封',
      back: '换个邮箱，重新来',
      as: '已登录 ', syncing: '同步中…', synced: (n) => `已同步 · 云端 ${n} 串`,
      sync: '再 次 同 步', out: '退 出', err: '出了点问题，稍后再试',
      bar: '串档目前只存在这台设备 · 登录后云端保存，换设备不丢', signin: '登 录' },
    en: { title: 'Cloud Archive', intro: 'Sign in, and your strands, calendar and reading place follow you on any device. A copy always stays here.',
      email: 'your email', send: 'Email Me a Code', sending: 'Sending…',
      sent: 'Email sent — type the 6-digit code below (or open the link on this device).',
      code: '6-digit code', verify: 'Sign In', verifying: 'Checking…',
      codeErr: 'Wrong or expired code — check it, or send a new one',
      back: 'Start over with another email',
      as: 'Signed in as ', syncing: 'Syncing…', synced: (n) => `Synced · ${n} strands in the cloud`,
      sync: 'Sync Again', out: 'Sign Out', err: 'Something went wrong, try again',
      bar: 'Your strands live only on this device — sign in to keep them in the cloud', signin: 'Sign In' },
    es: { title: 'Archivo en la Nube', intro: 'Inicia sesión y tus cuentas, calendario y lugar de lectura te siguen en cualquier dispositivo. Aquí siempre queda una copia.',
      email: 'tu correo', send: 'Enviarme un Código', sending: 'Enviando…',
      sent: 'Correo enviado: escribe abajo el código de 6 dígitos (o abre el enlace en este dispositivo).',
      code: 'código de 6 dígitos', verify: 'Entrar', verifying: 'Verificando…',
      codeErr: 'Código incorrecto o vencido: revísalo o envía uno nuevo',
      back: 'Empezar de nuevo con otro correo',
      as: 'Sesión: ', syncing: 'Sincronizando…', synced: (n) => `Sincronizado · ${n} cuentas en la nube`,
      sync: 'Sincronizar', out: 'Salir', err: 'Algo salió mal, inténtalo de nuevo',
      bar: 'Tus cuentas solo viven en este dispositivo — inicia sesión para guardarlas en la nube', signin: 'Iniciar Sesión' },
    pt: { title: 'Arquivo na Nuvem', intro: 'Entre, e suas contas, calendário e lugar de leitura seguem você em qualquer aparelho. Uma cópia sempre fica aqui.',
      email: 'seu e-mail', send: 'Enviar-me um Código', sending: 'Enviando…',
      sent: 'E-mail enviado — digite abaixo o código de 6 dígitos (ou abra o link neste aparelho).',
      code: 'código de 6 dígitos', verify: 'Entrar', verifying: 'Verificando…',
      codeErr: 'Código errado ou vencido — confira, ou envie um novo',
      back: 'Recomeçar com outro e-mail',
      as: 'Conectado: ', syncing: 'Sincronizando…', synced: (n) => `Sincronizado · ${n} contas na nuvem`,
      sync: 'Sincronizar', out: 'Sair', err: 'Algo deu errado, tente de novo',
      bar: 'Suas contas vivem só neste aparelho — entre para guardá-las na nuvem', signin: 'Entrar' },
  };
  const T = DICT[LANG] || DICT.en;

  // ---------- 骨架：右上角图标 + 下拉面板（不等库加载） ----------
  const ico = document.createElement('button');
  ico.id = 'acctIco'; ico.className = 'iconBtn';
  ico.setAttribute('aria-label', T.title);
  ico.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" ' +
    'stroke-linecap="round"><circle cx="12" cy="8.2" r="3.4"/>' +
    '<path d="M4.8 19.6c1.6-3.2 4.2-4.8 7.2-4.8s5.6 1.6 7.2 4.8"/></svg>';
  const panel = document.createElement('div');
  panel.id = 'acctPanel';
  panel.innerHTML = '<h3 style="margin:0 0 0.5em;font-size:0.85rem;letter-spacing:0.25em;' +
    'font-weight:normal;opacity:0.8;text-align:center">' + T.title + '</h3>' +
    '<div class="acctBody" style="font-size:0.82rem;line-height:2;text-align:center"></div>';
  document.body.appendChild(ico);
  document.body.appendChild(panel);

  // 账户 UI 已统一到右上角面板（工坊底部 Cloud Archive 区块 2026-07-23 移除）
  // 工坊页仍保留：进门未登录横幅 + 自动同步 + 拉到新串刷新
  const isWorkshop = /gongfang\.html$/.test(location.pathname);
  const bodies = () => document.querySelectorAll('.acctBody');

  ico.addEventListener('click', (ev) => {
    ev.stopPropagation();
    panel.classList.toggle('on');
    ensureLib();
  });
  document.addEventListener('click', (ev) => {
    if (panel.classList.contains('on') && !panel.contains(ev.target)) panel.classList.remove('on');
  });

  // ---------- 状态 ----------
  let client = null, me = null;

  function hasToken() {
    try { return Object.keys(localStorage).some((k) => /^sb-.+-auth-token$/.test(k)); }
    catch (_) { return false; }
  }
  function markIcon() { ico.classList.toggle('in', !!me || (!client && hasToken())); }

  // 工坊进门横幅（未登录才出现）
  let bar = null;
  function paintBar() {
    if (!isWorkshop) return;
    if (me) { if (bar) { bar.remove(); bar = null; } return; }
    if (bar) return;
    bar = document.createElement('button');
    bar.id = 'cloudBar';
    bar.innerHTML = '☁ ' + T.bar + ' →';
    bar.addEventListener('click', () => { panel.classList.add('on'); ensureLib(); });
    const h = document.querySelector('header') || document.body.firstElementChild;
    document.body.insertBefore(bar, h);
  }

  function viewSignedOut(note) {
    bodies().forEach((el) => {
      el.innerHTML =
        '<div>' + (note || T.intro) + '</div>' +
        '<input class="cloudEmail" type="email" placeholder="' + T.email + '" style="width:100%;' +
        'box-sizing:border-box;margin-top:0.7em;padding:0.6em 1em;border-radius:2em;border:1px solid rgba(245,205,138,0.5);' +
        'background:rgba(253,243,227,0.08);color:inherit;font-family:inherit;font-size:0.85rem;text-align:center">' +
        '<div style="margin-top:0.7em"><button class="cloudSend" style="font-family:inherit;cursor:pointer;' +
        'border-radius:2em;padding:0.5em 1.6em;border:1px solid rgba(245,205,138,0.7);' +
        'background:rgba(245,205,138,0.12);color:inherit;font-size:0.82rem">' + T.send + '</button></div>';
      el.querySelector('.cloudSend').addEventListener('click', async () => {
        const email = el.querySelector('.cloudEmail').value.trim();
        if (!email) return;
        el.querySelector('.cloudSend').textContent = T.sending;
        if (!client) { await ensureLib(); }
        const { error } = await client.auth.signInWithOtp({
          email: email,
          options: { emailRedirectTo: location.origin + location.pathname },
        });
        if (error) {
          el.innerHTML = '<div>' + T.err + '<br><span style="opacity:0.6">' +
            (error.message || '') + '</span></div>';
          return;
        }
        // 发送成功 → 就地输 6 位码登录（解决"手机发的链接在电脑上点开"的跨设备问题）
        el.innerHTML =
          '<div>' + T.sent + '</div>' +
          '<input class="cloudCode" type="text" inputmode="numeric" autocomplete="one-time-code" ' +
          'maxlength="6" placeholder="' + T.code + '" style="width:11em;box-sizing:border-box;' +
          'margin-top:0.7em;padding:0.6em 1em;border-radius:2em;border:1px solid rgba(245,205,138,0.5);' +
          'background:rgba(253,243,227,0.08);color:inherit;font-family:inherit;font-size:1.05rem;' +
          'text-align:center;letter-spacing:0.35em">' +
          '<div style="margin-top:0.7em"><button class="cloudVerify" style="font-family:inherit;' +
          'cursor:pointer;border-radius:2em;padding:0.5em 1.8em;border:1px solid rgba(245,205,138,0.7);' +
          'background:rgba(245,205,138,0.12);color:inherit;font-size:0.82rem">' + T.verify + '</button></div>' +
          '<div class="codeMsg" style="margin-top:0.4em;font-size:0.76rem;opacity:0.75"></div>' +
          '<button class="cloudBack" style="background:none;border:none;cursor:pointer;' +
          'font-family:inherit;color:inherit;opacity:0.55;font-size:0.74rem;margin-top:0.5em;' +
          'text-decoration:underline">' + T.back + '</button>';
        const doVerify = async () => {
          const code = el.querySelector('.cloudCode').value.replace(/\D/g, '');
          if (code.length !== 6) return;
          el.querySelector('.cloudVerify').textContent = T.verifying;
          const { error: e2 } = await client.auth.verifyOtp({ email: email, token: code, type: 'email' });
          if (e2) {
            el.querySelector('.cloudVerify').textContent = T.verify;
            el.querySelector('.codeMsg').textContent = T.codeErr;
          }
          // 成功则 SIGNED_IN 事件自动接管（切登录视图 + 同步）
        };
        el.querySelector('.cloudVerify').addEventListener('click', doVerify);
        el.querySelector('.cloudCode').addEventListener('keydown', (ev2) => {
          if (ev2.key === 'Enter') doVerify();
        });
        el.querySelector('.cloudBack').addEventListener('click', () => viewSignedOut());
        el.querySelector('.cloudCode').focus();
      });
    });
    paintBar();
    markIcon();
  }

  function viewSignedIn(status) {
    bodies().forEach((el) => {
      el.innerHTML =
        '<div style="opacity:0.9">' + T.as + '<span style="color:#f5cd8a;word-break:break-all">' +
        (me.email || '') + '</span></div>' +
        '<div class="cloudStat" style="margin-top:0.4em">' + (status || '') + '</div>' +
        '<div style="margin-top:0.8em">' +
        '<button class="cloudSync" style="font-family:inherit;cursor:pointer;border-radius:2em;' +
        'padding:0.45em 1.4em;border:1px solid rgba(245,205,138,0.7);background:rgba(245,205,138,0.12);' +
        'color:inherit;font-size:0.8rem;margin:0 0.3em">' + T.sync + '</button>' +
        '<button class="cloudOut" style="font-family:inherit;cursor:pointer;border-radius:2em;' +
        'padding:0.45em 1.4em;border:1px solid rgba(253,243,227,0.4);background:none;' +
        'color:inherit;font-size:0.8rem;margin:0 0.3em">' + T.out + '</button></div>';
      el.querySelector('.cloudSync').addEventListener('click', () => runSync(true));
      el.querySelector('.cloudOut').addEventListener('click', async () => {
        await client.auth.signOut();
        me = null;
        viewSignedOut();
      });
    });
    paintBar();
    markIcon();
  }

  function setStat(text) {
    document.querySelectorAll('.cloudStat').forEach((el) => { el.textContent = text; });
  }

  // ---------- 同步 ----------
  function pairKeyOf(e) {
    try { return e.meta.wall.map((w) => w[0] + w[1]).sort().join('|'); } catch (_) { return null; }
  }
  function cloudToLocal(c, oldE) {
    return {
      pairId: (oldE && oldE.pairId) || ('cloud-' + c.pair_key),
      label: (oldE && oldE.label) || '',
      refs: c.refs || [], anchors: c.anchors || [], anchorsB: c.anchors_b || [],
      reason: c.reason || '', pub: !!c.is_public, date: c.strung_on, meta: c.meta || {},
    };
  }

  // 轻状态同步：串珠历逐日取最大（可交换合并，无需时间戳）；
  // 读经位置按语言各存一键（reading:zh / reading:en…），当前使用中的设备为准
  async function syncStates() {
    const KD = 'days', KR = 'reading:' + LANG;
    let days = {}, reading = null;
    try { days = JSON.parse(localStorage.getItem('chuanzhu_days')) || {}; } catch (_) {}
    try { reading = JSON.parse(localStorage.getItem('chuanzhu_reading')); } catch (_) {}
    const { data: rows, error } = await client.from('states')
      .select('key,value').in('key', [KD, KR]);
    if (error) throw error;
    const cloud = {};
    for (const r of rows) cloud[r.key] = r.value || {};
    const md = Object.assign({}, cloud[KD]);
    for (const d in days) md[d] = Math.max(md[d] || 0, days[d]);
    localStorage.setItem('chuanzhu_days', JSON.stringify(md));
    const ups = [{ user_id: me.id, key: KD, value: md,
                   updated_at: new Date().toISOString() }];
    if (reading && reading.bk) {
      ups.push({ user_id: me.id, key: KR, value: reading,
                 updated_at: new Date().toISOString() });
    } else if (cloud[KR] && cloud[KR].bk) {
      localStorage.setItem('chuanzhu_reading', JSON.stringify(cloud[KR]));
    }
    await client.from('states').upsert(ups, { onConflict: 'user_id,key' });
  }

  // 合并策略：按章对键对齐，日期新者胜；云端独有的拉下来，本机新的推上去
  // 换账号防污染：本机串档记归属（chuanzhu_owner）——归属是别人时不上传，清本机、以新账号云端为准
  async function runSync(manual) {
    setStat(T.syncing);
    try {
      await client.from('profiles').upsert(
        { id: me.id, display_name: (me.email || '').split('@')[0] });
      let switched = false;
      try {
        const o = localStorage.getItem('chuanzhu_owner');
        switched = !!(o && o !== me.id);
      } catch (_) {}
      if (switched) {
        for (const k of ['chuanzhu_strings', 'chuanzhu_days', 'chuanzhu_daylog',
                         'chuanzhu_reading', 'chuanzhu_lastch', 'wall1189']) {
          try { localStorage.removeItem(k); } catch (_) {}
        }
      }
      let local = [];
      try { local = JSON.parse(localStorage.getItem('chuanzhu_strings')) || []; } catch (_) {}
      const { data: cloud, error } = await client.from('strands')
        .select('pair_key,refs,anchors,anchors_b,reason,is_public,lang,meta,strung_on');
      if (error) throw error;
      const cmap = new Map();
      for (const c of cloud) cmap.set(c.pair_key, c);
      const merged = [], ups = [], seen = new Set();
      let pulled = 0;
      for (const e of local) {
        const k = pairKeyOf(e);
        if (!k) { merged.push(e); continue; }
        seen.add(k);
        const c = cmap.get(k);
        if (!c || (e.date || '') >= (c.strung_on || '')) {
          ups.push({
            user_id: me.id, pair_key: k, refs: e.refs || [],
            anchors: e.anchors || [], anchors_b: e.anchorsB || [],
            reason: e.reason || '', is_public: !!e.pub, lang: LANG, meta: e.meta || {},
            strung_on: e.date || new Date().toISOString().slice(0, 10),
            updated_at: new Date().toISOString(),
          });
          merged.push(e);
        } else {
          merged.push(cloudToLocal(c, e)); pulled++;
        }
      }
      for (const [k, c] of cmap) if (!seen.has(k)) { merged.push(cloudToLocal(c, null)); pulled++; }
      if (ups.length) {
        const { error: e2 } = await client.from('strands')
          .upsert(ups, { onConflict: 'user_id,pair_key' });
        if (e2) throw e2;
      }
      merged.sort((a, b) => (b.date || '').localeCompare(a.date || ''));
      localStorage.setItem('chuanzhu_strings', JSON.stringify(merged));
      // 换账号后从云端重建点亮墙（墙不入云，靠串档的 wall 元数据回放）
      if (switched) {
        const w = {};
        for (const e of merged) {
          if (e.meta && e.meta.wall) for (const bc of e.meta.wall) w[bc[0] + bc[1]] = 4;
        }
        try { localStorage.setItem('wall1189', JSON.stringify(w)); } catch (_) {}
      }
      try { localStorage.setItem('chuanzhu_owner', me.id); } catch (_) {}
      try { await syncStates(); } catch (_) {} // 轻状态失败不拦主同步
      const total = merged.filter((e) => pairKeyOf(e)).length;
      setStat(T.synced(total));
      // 云端拉下了新串（或换了账号）→ 刷新页面让挂串墙重绘
      if ((pulled > 0 || switched) && isWorkshop && !manual) location.reload();
      if ((pulled > 0 || switched) && isWorkshop && manual) setTimeout(() => location.reload(), 900);
    } catch (err) {
      setStat(T.err + ' · ' + ((err && err.message) || ''));
    }
  }

  // ---------- 库加载与初始化 ----------
  let libP = null;
  function ensureLib() {
    if (libP) return libP;
    libP = new Promise((resolve) => {
      const s = document.createElement('script');
      s.src = 'https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js';
      s.onload = () => { init(); resolve(); };
      s.onerror = () => { resolve(); };
      document.head.appendChild(s);
    });
    return libP;
  }

  // 幂等进入登录态：doSync 控制是否自动同步（恢复会话只在工坊页自动同步；新登录任何页都同步）
  function enter(user, doSync) {
    if (me && me.id === user.id) return;
    me = user;
    viewSignedIn(doSync ? T.syncing : '');
    if (doSync) runSync(false);
  }

  function init() {
    if (client) return;
    client = window.supabase.createClient(SUPA_URL, SUPA_KEY);
    client.auth.getSession().then(({ data }) => {
      if (data && data.session) enter(data.session.user, isWorkshop);
      // 已是未登录视图时不重绘——避免把正在输入的邮箱框刷掉
    });
    client.auth.onAuthStateChange((event, session) => {
      if (event === 'SIGNED_IN' && session) enter(session.user, true);
    });
  }

  // P2b：读一颗珠上众人公开的注脚——任何人可看（2026-07-23 用户定，折叠链接保留"先自己想"的摩擦）
  // 已登录走 SDK（带 mine 标记）；未登录走轻量 REST（不为访客加载 50KB SDK）
  window.cloudNotes = function (pairKey) {
    if (client && me) {
      return client.rpc('bead_notes', { p_pair_key: pairKey })
        .then(({ data, error }) => (error ? null : data));
    }
    return fetch(SUPA_URL + '/rest/v1/rpc/bead_notes', {
      method: 'POST',
      headers: { apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY,
                 'Content-Type': 'application/json' },
      body: JSON.stringify({ p_pair_key: pairKey }),
    }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  };
  // 造就了我：登录后可点/可收回
  window.cloudAmen = function (sid, on) {
    if (!client || !me) return Promise.resolve(false);
    const q = on
      ? client.from('amens').insert({ strand_id: sid, user_id: me.id })
      : client.from('amens').delete().eq('strand_id', sid).eq('user_id', me.id);
    return q.then(({ error }) => !error);
  };
  window.cloudSignedIn = function () { return !!(client && me); };
  // 社区线：读（任何人，轻量 REST）；提交（登录）——同线已存在则记一票附议
  window.cloudThreads = function (beadKey) {
    return fetch(SUPA_URL + '/rest/v1/threads?select=id,verse_a,verse_b,words,lang' +
      '&bead_key=eq.' + encodeURIComponent(beadKey) + '&status=eq.live&order=created_at',
      { headers: { apikey: SUPA_KEY, Authorization: 'Bearer ' + SUPA_KEY } })
      .then((r) => (r.ok ? r.json() : null)).catch(() => null);
  };
  window.cloudSubmitThread = function (beadKey, va, vb, words) {
    if (!client || !me) return Promise.resolve('signin');
    return client.from('threads').insert({
      bead_key: beadKey, verse_a: va, verse_b: vb,
      words: words || {}, creator: me.id, lang: LANG,
    }).then(({ error }) => {
      if (!error) return 'new';
      if (error.code !== '23505') return 'err';
      return client.from('threads').select('id')
        .eq('bead_key', beadKey).eq('verse_a', va).eq('verse_b', vb).single()
        .then(({ data }) => (data
          ? client.from('thread_amens').insert({ thread_id: data.id, user_id: me.id })
              .then(({ error: e2 }) => ((!e2 || e2.code === '23505') ? 'second' : 'err'))
          : 'err'));
    });
  };

  // 首屏：有会话或魔法链接回跳 → 立即加载库；否则骨架即可（点开图标再加载）
  viewSignedOut();
  markIcon();
  if (hasToken() || location.hash.indexOf('access_token') >= 0 || /[?&]code=/.test(location.search)) {
    ensureLib();
  }
})();

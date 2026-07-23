/* 场景预设 —— 每个场景就是一份参数包
 * 引擎原子：天空 / 地形 / 水面 / 道具 / 粒子 / 音频 / 行走 / 灵修流程
 */
window.SCENES = {

  // ------------------------------------------------ 旷野（何西阿 2:14）
  wilderness: {
    id: 'wilderness',
    title: '旷 野',
    subtitle: '一 次 五 分 钟 的 沙 漠 灵 修',
    palette: {
      zenith: '#7d8fb3', horizon: '#f0c8a2', sun: '#ffe3b8',
      ground: '#d8b88e', fog: '#f0c8a2',
    },
    sky: { sunDir: [-0.22, 0.10, -1], sunIntensity: 1.15, stars: 0.35,
           hemi: { sky: '#8fa3c4', ground: '#caa87e', intensity: 0.65 } },
    ui: { scrim: 0.15 },
    fogRange: [70, 430],
    terrain: { kind: 'dunes', amp: 1.0, corridor: 18, color: '#d8b88e' },
    water: null,
    props: [
      { kind: 'rocks', color: '#5d4a3c', spots: [
        [-34, 20], [28, -8], [-52, -46], [45, -70], [-23, -105],
        [60, -140], [-70, -170], [19, -195], [-38, -240], [75, -60]] },
      { kind: 'tree', pos: [7, -150], trunkColor: '#4d453a', leafColor: '#5a5c42' },
    ],
    particles: { color: '#e8d0a8', count: 320, size: 0.05, opacity: 0.55, drift: 1.2 },
    audio: { layers: [
      // 风：低频轰鸣，LFO 调制滤波频率（呼啸感）
      { type: 'lowpass', freq: 420, q: 0.4, gain: 0.22,
        lfo: { target: 'freq', hz: 0.06, depth: 180 } },
    ] },
    walk: { x: 0, startZ: 55, speed: 0.58 },
    flow: {
      pre: ['你走了很远的路，来到这里。', '先让呼吸慢下来。'],
      capsule: [
        '两千七百年前，以色列远离了她的神。',
        '神没有用责备把她追回来——',
        '祂选择把她带到一个安静的地方。'],
      verses: ['「后来我必劝导她，', '领她到旷野，', '对她说安慰的话。」'],
      attribution: '—— 何西阿书 2:14（和合本）',
      stillLine: '此刻，只有风声。',
      meditation: ['如果神此刻要对你说一句安慰的话，', '你觉得，会是哪一句？'],
      bridge: '把它放在心里，带出旷野。',
      closingBig: '今日的旷野，已点亮',
      closingDim: '「领她到旷野，对她说安慰的话。」<br>明天，旷野会换一个地方。',
    },
  },

  // ------------------------------------------------ 水边（诗篇 23）
  stillwaters: {
    id: 'stillwaters',
    title: '水 边',
    subtitle: '一 次 五 分 钟 的 安 歇',
    palette: {
      zenith: '#6fa8d8', horizon: '#e9f2e2', sun: '#fffbee',
      ground: '#74915c', fog: '#e9f2e2',
    },
    sky: { sunDir: [0.5, 0.2, -0.8], sunIntensity: 0.95, stars: 0,
           hemi: { sky: '#9cc6e2', ground: '#5f7d4a', intensity: 0.8 } },
    ui: { scrim: 0.28 },
    fogRange: [70, 420],
    terrain: { kind: 'shore', color: '#74915c', shore: [-2, 22], roll: 0.9,
      // 按高度上色：水下泥色 → 湿岸深绿 → 草坡翠绿 → 高处黄绿
      ramp: [[-6, '#3d5244'], [-0.2, '#48604a'], [0.4, '#5c7d4c'],
             [1.8, '#74995a'], [3.6, '#93a86a']] },
    water: { level: 0, color: '#3e7d92', opacity: 0.9,
             waveAmp: 0.09, waveFreq: 0.35, speed: 0.7 },
    props: [
      { kind: 'rocks', color: '#78786a', spots: [
        [-44, -20], [-60, -90], [-34, -160], [-68, -210], [-28, 30]] },
      { kind: 'tree', pos: [-4, -150], dest: true, trunkColor: '#55452f', leafColor: '#4e7040' },
      { kind: 'tree', pos: [-26, -60],  trunkColor: '#55452f', leafColor: '#5a7e48' },
      { kind: 'tree', pos: [-38, -120], trunkColor: '#55452f', leafColor: '#476b3c' },
      { kind: 'tree', pos: [-20, -220], trunkColor: '#55452f', leafColor: '#5a7e48' },
      { kind: 'bushes', color: '#4c6b3e', spots: [
        [-16, -30], [-8, -70], [-22, -95], [-12, -130], [-30, -75],
        [-18, -180], [-7, -105], [-25, -205], [-14, 15]] },
      { kind: 'reeds', color: '#3f5c34', clusters: [
        [1, 20], [3, -15], [0, -48], [2, -80], [4, -110], [1, -138], [3, -170], [2, -195]] },
      { kind: 'clouds', color: '#f7fbff', spots: [
        [120, 70, -320, 9], [30, 85, -380, 12], [-90, 62, -300, 7],
        [200, 78, -260, 10], [-40, 90, -420, 14]] },
    ],
    particles: { color: '#ffffff', count: 160, size: 0.14, opacity: 0.18, drift: 0.35 },
    audio: { layers: [
      // 远处湖面的低鸣（很轻的底）
      { type: 'lowpass', freq: 360, q: 0.5, gain: 0.07,
        lfo: { target: 'gain', hz: 0.11, depth: 0.03 } },
      // 拍岸：中频，音量按节奏起伏——水声的骨架
      { type: 'bandpass', freq: 950, q: 1.1, gain: 0.13,
        lfo: { target: 'gain', hz: 0.33, depth: 0.09 } },
      // 粼粼细响：高频，快而浅的闪烁
      { type: 'bandpass', freq: 2700, q: 2.2, gain: 0.05,
        lfo: { target: 'gain', hz: 0.61, depth: 0.035 } },
    ] },
    walk: { x: -9, startZ: 55, speed: 0.55 },
    flow: {
      pre: ['从人声鼎沸的地方，你来到水边。', '先让呼吸慢下来。'],
      capsule: [
        '写这首诗的人，做过牧羊人。',
        '他知道：羊只有在完全安全的时候，才肯躺下。',
        '后来他作了王，却说——真正的牧者，不是我。'],
      verses: ['「耶和华是我的牧者，', '我必不至缺乏。', '他使我躺卧在青草地上，', '领我在可安歇的水边。」'],
      attribution: '—— 诗篇 23:1-2',
      stillLine: '此刻，只有水声。',
      meditation: ['这一周，是什么让你不得安歇？', '把它交给牧者，在这里躺卧片刻。'],
      bridge: '他使我的灵魂苏醒。',
      closingBig: '今日的水边，已点亮',
      closingDim: '「他使我的灵魂苏醒。」<br>明天，可以再来水边。',
    },
  },

  // ------------------------------------------------ 蓖麻树下（约拿 4）—— 完整闭环示范：场景+读经+答题+点亮
  jonah: {
    id: 'jonah',
    title: '蓖 麻 树 下',
    subtitle: '约 拿 书 · 城 外 的 问 题',
    palette: {
      zenith: '#8298a8', horizon: '#e3c99e', sun: '#ffedc2',
      ground: '#c3a87e', fog: '#e3c99e',
    },
    sky: { sunDir: [0.18, 0.4, -0.85], sunIntensity: 1.0, stars: 0,
           hemi: { sky: '#9aa8b2', ground: '#b49c74', intensity: 0.6 } },
    ui: { scrim: 0.42 },
    fogRange: [60, 400],
    terrain: { kind: 'dunes', amp: 0.55, corridor: 20, color: '#cdb489' },
    water: null,
    props: [
      { kind: 'rocks', color: '#8a7a62', spots: [
        [-30, 15], [26, -30], [-48, -70], [40, -110], [-22, -145],
        [55, -180], [-60, -200], [18, -230]] },
      // 那棵蓖麻树：目的地
      { kind: 'tree', pos: [6, -140], dest: true, trunkColor: '#77613f', leafColor: '#6d8440' },
      // 地平线上的尼尼微（藏在热雾里）
      { kind: 'city', color: '#a08e74', center: [-130, -340], n: 26 },
    ],
    particles: { color: '#eeddb8', count: 360, size: 0.05, opacity: 0.5, drift: 1.7 },
    audio: { layers: [
      // 燥热的东风：比旷野更闷更沉
      { type: 'lowpass', freq: 360, q: 0.5, gain: 0.2,
        lfo: { target: 'freq', hz: 0.05, depth: 140 } },
      // 偶尔的高频热风啸
      { type: 'bandpass', freq: 1900, q: 3.2, gain: 0.022,
        lfo: { target: 'gain', hz: 0.09, depth: 0.018 } },
    ] },
    walk: { x: 0, startZ: 50, speed: 0.6 },
    wallTarget: { '拿3': 1, '拿4': 2 },   // 完成本课：拿3 初亮，拿4 达"观察"
    flow: {
      pre: ['尼尼微在你身后，日头正烈。', '你为一件"好事"在生气。'],
      capsule: [
        '先知约拿刚经历了一场「失败」：',
        '他宣告的审判没有降临——因为尼尼微悔改了。',
        '神赦免了约拿最恨的仇敌。他气得求死，独自坐在城外。'],
      verses: [
        '「耶和华神安排一棵蓖麻，',
        '使其发生高过约拿，影儿遮盖他的头，',
        '救他脱离苦楚；',
        '约拿因这棵蓖麻大大喜乐。」'],
      attribution: '—— 约拿书 4:6（和合本）',
      stillLine: '此刻，只有燥热的风。',
      meditation: [
        '「次日黎明，神却安排一条虫子咬这蓖麻，以致枯槁。」',
        '神问约拿——也问每一个坐在城外的人：',
        '「你这样发怒合乎理吗？」'],
      bridge: '这卷书停在问号上。回应几个问题，再走。',
      quiz: [
        { tag: '观 察', q: '约拿为什么向耶和华发怒？',
          opts: [
            { t: '因为尼尼微人没有听他传的信息' },
            { t: '因为神看见尼尼微人悔改，就不降所说的灾', ok: true },
            { t: '因为船员曾把他抛进海里' },
            { t: '因为蓖麻树枯槁了' }],
          source: '拿 4:1-2（和合本）',
          explain: '他自己说出了原因：「我知道你是有恩典、有怜悯的神，不轻易发怒，有丰盛的慈爱，并且后悔不降所说的灾。」（拿 4:2）他不是怕失败，是怕神赦免。',
          hint: '再读拿 4:1-2——蓖麻枯槁是他第二次发怒的原因（4:9）。' },
        { tag: '解 释', q: '神让蓖麻树一夜生长、次日枯槁，是要约拿明白什么？',
          opts: [
            { t: '大自然无常，万物都会朽坏' },
            { t: '他爱惜一棵不劳而得的树，神岂不更爱惜城里的十二万人', ok: true },
            { t: '这是对他抱怨的惩罚' },
            { t: '神有能力掌管一切植物' }],
          source: '拿 4:10-11（和合本）',
          explain: '「何况这尼尼微大城，其中不能分辨左手右手的有十二万多人，并有许多牲畜，我岂能不爱惜呢？」（拿 4:10-11）',
          hint: '蓖麻和尼尼微，在神的问话里是一组对比（4:10-11）。' },
        { tag: '开 放 · 没 有 标 准 答 案', q: '全书停在神的问句上，没有记载约拿的回答。你怎么读这个结尾？', open: true,
          opts: [
            { t: '这是留给读者的位置——问题其实在问每一个「我」',
              fb: '教会传统普遍这样读：全书最后一节，是神把笔递给了你。' },
            { t: '约拿写下这卷书、把自己写成反面人物——这本身就是他的回答',
              fb: '犹太传统在赎罪日下午诵读约拿书——它被放在「悔改」的位置上。' },
            { t: '约拿也许至死没有转过弯来——这个结尾诚实得可怕',
              fb: '它与路加福音 15 章平行：父亲出来劝大儿子，故事同样停在门外。' },
            { t: '重点是神竟肯与使性子的先知反复对话——问句本身就是恩典',
              fb: '整卷书里，神安排了大鱼、蓖麻、虫和东风——祂从头到尾没有放弃这位先知。' }],
        },
      ],
      closingBig: '拿 4 · 观察，已点亮',
      closingDim: '「我岂能不爱惜呢？」（拿 4:11）<br>去墙上看看——约拿书亮起来了。',
    },
  },
};

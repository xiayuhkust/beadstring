/* 场景引擎 —— 读取 window.SCENES 中的预设，构建天空/地形/水面/道具/粒子/音频/灵修流程
 * 零构建，three.js r147 (UMD, 本地)。切换场景：?scene=wilderness | stillwaters
 */

// ---------------------------------------------------------------- 预设选择

const sceneKey = new URLSearchParams(location.search).get('scene') || 'wilderness';
const P = window.SCENES[sceneKey] || window.SCENES.wilderness;

document.title = P.title.replace(/\s/g, '') + ' · 灵修场景';
document.getElementById('sceneTitle').textContent = P.title;
document.getElementById('sceneSub').textContent = P.subtitle;
// 亮场景的字幕底衬强度（0 = 无）
document.getElementById('text').style.setProperty('--scrim', (P.ui && P.ui.scrim) || 0);

// ---------------------------------------------------------------- 基础

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputEncoding = THREE.sRGBEncoding;

const scene = new THREE.Scene();
const C = (hex) => new THREE.Color(hex);

scene.fog = new THREE.Fog(C(P.palette.fog).getHex(), P.fogRange[0], P.fogRange[1]);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 2000);
const sunDir = new THREE.Vector3(...P.sky.sunDir).normalize();

// ---------------------------------------------------------------- 天空

const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide,
  depthWrite: false,
  uniforms: {
    topColor:     { value: C(P.palette.zenith) },
    horizonColor: { value: C(P.palette.horizon) },
    sunColor:     { value: C(P.palette.sun) },
    sunDir:       { value: sunDir },
  },
  vertexShader: `
    varying vec3 vDir;
    void main() {
      vDir = normalize(position);
      gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
    }`,
  fragmentShader: `
    uniform vec3 topColor, horizonColor, sunColor;
    uniform vec3 sunDir;
    varying vec3 vDir;
    void main() {
      vec3 d = normalize(vDir);
      float h = max(d.y, 0.0);
      vec3 sky = mix(horizonColor, topColor, pow(h, 0.55));
      float sunDot = max(dot(d, sunDir), 0.0);
      float disc = pow(sunDot, 900.0) * 1.4;
      float halo = pow(sunDot, 7.0)   * 0.28;
      gl_FragColor = vec4(sky + sunColor * (disc + halo), 1.0);
    }`,
});
scene.add(new THREE.Mesh(new THREE.SphereGeometry(900, 32, 20), skyMat));

// 残星
if (P.sky.stars > 0) {
  const n = 220, pos = new Float32Array(n * 3);
  for (let i = 0; i < n; i++) {
    const az = Math.random() * Math.PI * 2;
    const el = 0.25 + Math.random() * 1.2;
    pos[i*3]   = Math.cos(az) * Math.cos(el) * 800;
    pos[i*3+1] = Math.sin(el) * 800;
    pos[i*3+2] = Math.sin(az) * Math.cos(el) * 800;
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  scene.add(new THREE.Points(g, new THREE.PointsMaterial({
    color: 0xfff5e0, size: 1.6, sizeAttenuation: false,
    transparent: true, opacity: P.sky.stars, fog: false, depthWrite: false,
  })));
}

// ---------------------------------------------------------------- 地形

function smoothstep(a, b, x) {
  const t = Math.min(Math.max((x - a) / (b - a), 0), 1);
  return t * t * (3 - 2 * t);
}

function makeHeightFn(t) {
  if (t.kind === 'dunes') {
    return (x, z) => {
      let h = 0;
      h += 3.4 * Math.sin(x * 0.021 + Math.sin(z * 0.013) * 1.7);
      h += 2.2 * Math.sin(z * 0.016 + Math.sin(x * 0.011) * 2.3);
      h += 0.9 * Math.sin(x * 0.061 + z * 0.043);
      h += 0.35 * Math.sin(x * 0.13 - z * 0.11);
      h *= t.amp;
      const corridor = Math.exp(-(x * x) / (2 * t.corridor * t.corridor));
      return h * (1 - 0.5 * corridor);
    };
  }
  if (t.kind === 'shore') {
    // 左岸缓坡草地，x 越大越向湖心下沉；水面在 y=0
    const [s0, s1] = t.shore || [-2, 22];
    return (x, z) => {
      const rolling = (1.1 * Math.sin(z * 0.028 + Math.sin(x * 0.02) * 1.4)
                    + 0.5 * Math.sin(x * 0.06 + z * 0.045)) * (t.roll || 1);
      const toLake = smoothstep(s0, s1, x);
      return 1.8 + rolling - toLake * 7.5;
    };
  }
  return () => 0;
}

const heightFn = makeHeightFn(P.terrain);

{
  const geo = new THREE.PlaneGeometry(900, 900, 170, 170);
  geo.rotateX(-Math.PI / 2);
  const pos = geo.attributes.position;
  for (let i = 0; i < pos.count; i++) {
    pos.setY(i, heightFn(pos.getX(i), pos.getZ(i)));
  }
  geo.computeVertexNormals();
  const matOpts = { roughness: 1.0, metalness: 0.0, flatShading: true };
  if (P.terrain.ramp) {
    // 按高度上色：近水湿绿 → 草坡翠绿 → 高处干绿
    const stops = P.terrain.ramp.map(([h, c]) => [h, new THREE.Color(c)]);
    const colors = new Float32Array(pos.count * 3);
    for (let i = 0; i < pos.count; i++) {
      const h = pos.getY(i);
      let col = stops[0][1];
      if (h >= stops[stops.length - 1][0]) {
        col = stops[stops.length - 1][1];
      } else {
        for (let s = 0; s < stops.length - 1; s++) {
          if (h >= stops[s][0] && h < stops[s + 1][0]) {
            const f = (h - stops[s][0]) / (stops[s + 1][0] - stops[s][0]);
            col = stops[s][1].clone().lerp(stops[s + 1][1], f);
            break;
          }
        }
      }
      colors[i*3] = col.r; colors[i*3+1] = col.g; colors[i*3+2] = col.b;
    }
    geo.setAttribute('color', new THREE.BufferAttribute(colors, 3));
    matOpts.vertexColors = true;
    matOpts.color = 0xffffff;
  } else {
    matOpts.color = C(P.terrain.color);
  }
  scene.add(new THREE.Mesh(geo, new THREE.MeshStandardMaterial(matOpts)));
}

// ---------------------------------------------------------------- 水面

let water = null;
if (P.water) {
  const W = P.water;
  const geo = new THREE.PlaneGeometry(700, 700, 80, 80);
  geo.rotateX(-Math.PI / 2);
  water = new THREE.Mesh(geo, new THREE.MeshStandardMaterial({
    color: C(W.color), roughness: 0.32, metalness: 0.1, flatShading: true,
    transparent: true, opacity: W.opacity,
  }));
  water.position.set(0, W.level, -100);
  scene.add(water);
}

// ---------------------------------------------------------------- 道具

const propBuilders = {
  rocks(p) {
    const mat = new THREE.MeshStandardMaterial({ color: C(p.color), roughness: 1, flatShading: true });
    for (const [x, z] of p.spots) {
      const s = 0.8 + (((x * 7 + z * 13) % 10 + 10) % 10) * 0.22;
      const rock = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), mat);
      rock.position.set(x, heightFn(x, z) + s * 0.3, z);
      rock.rotation.set(x, z, x + z);
      rock.scale.y = 0.65;
      scene.add(rock);
    }
  },
  tree(p) {
    const dark = new THREE.MeshStandardMaterial({ color: C(p.trunkColor), roughness: 1, flatShading: true });
    const leaf = new THREE.MeshStandardMaterial({ color: C(p.leafColor), roughness: 1, flatShading: true });
    const tree = new THREE.Group();
    const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.3, 3.4, 6), dark);
    trunk.position.y = 1.7; trunk.rotation.z = 0.08;
    const c1 = new THREE.Mesh(new THREE.ConeGeometry(2.6, 0.9, 7), leaf);
    c1.position.set(0.3, 3.55, 0);
    const c2 = new THREE.Mesh(new THREE.ConeGeometry(1.7, 0.7, 6), leaf);
    c2.position.set(-0.7, 3.1, 0.5);
    tree.add(trunk, c1, c2);
    tree.position.set(p.pos[0], heightFn(p.pos[0], p.pos[1]), p.pos[1]);
    scene.add(tree);
  },
  bushes(p) {
    const mat = new THREE.MeshStandardMaterial({ color: C(p.color), roughness: 1, flatShading: true });
    for (const [x, z] of p.spots) {
      const s = 0.6 + (((x * 5 + z * 11) % 10 + 10) % 10) * 0.12;
      const bush = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), mat);
      bush.position.set(x, heightFn(x, z) + s * 0.35, z);
      bush.rotation.set(z, x, x * z);
      bush.scale.y = 0.55;
      scene.add(bush);
    }
  },
  clouds(p) {
    const mat = new THREE.MeshStandardMaterial({ color: C(p.color), roughness: 1, flatShading: true });
    for (const [x, y, z, s] of p.spots) {
      const cloud = new THREE.Group();
      const n = 3 + (Math.abs(x + z) % 3);
      for (let i = 0; i < n; i++) {
        const puff = new THREE.Mesh(new THREE.IcosahedronGeometry(s * (0.6 + (i % 3) * 0.25), 0), mat);
        puff.position.set(i * s * 0.9 - n * s * 0.4, Math.sin(i * 2.1) * s * 0.15, Math.cos(i * 1.7) * s * 0.3);
        puff.scale.y = 0.42;
        cloud.add(puff);
      }
      cloud.position.set(x, y, z);
      scene.add(cloud);
    }
  },
  city(p) {
    // 地平线上的城市剪影（藏在雾里）
    const mat = new THREE.MeshStandardMaterial({ color: C(p.color), roughness: 1, flatShading: true });
    const [cx, cz] = p.center;
    for (let i = 0; i < p.n; i++) {
      const w = 6 + ((i * 13) % 9), h = 8 + ((i * 29) % 26), d = 6 + ((i * 7) % 8);
      const b = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), mat);
      const x = cx + Math.sin(i * 2.7) * 90 + (i - p.n / 2) * 7;
      const z = cz + Math.cos(i * 1.9) * 40;
      b.position.set(x, heightFn(x, z) + h / 2 - 1, z);
      scene.add(b);
    }
  },
  reeds(p) {
    const mat = new THREE.MeshStandardMaterial({ color: C(p.color), roughness: 1, flatShading: true });
    for (const [cx, cz] of p.clusters) {
      const n = 5 + ((cx + cz * 3) % 4 + 4) % 4;
      for (let i = 0; i < n; i++) {
        const x = cx + Math.sin(i * 2.4 + cz) * 0.6;
        const z = cz + Math.cos(i * 1.9 + cx) * 0.6;
        const h = 0.9 + ((i * 37 + cx) % 10) * 0.06;
        const reed = new THREE.Mesh(new THREE.ConeGeometry(0.035, h, 4), mat);
        reed.position.set(x, heightFn(x, z) + h / 2, z);
        reed.rotation.set(Math.sin(i) * 0.08, 0, Math.cos(i * 3) * 0.08);
        scene.add(reed);
      }
    }
  },
};
for (const prop of P.props) propBuilders[prop.kind]?.(prop);

// 行走目的地 = 标记 dest 的树（无则第一棵树，再无则取远方）
const treeProp = P.props.find(p => p.kind === 'tree' && p.dest) || P.props.find(p => p.kind === 'tree');
const DEST = treeProp
  ? new THREE.Vector3(treeProp.pos[0], 0, treeProp.pos[1])
  : new THREE.Vector3(P.walk.x, 0, -150);

// ---------------------------------------------------------------- 光

const sun = new THREE.DirectionalLight(C(P.palette.sun), P.sky.sunIntensity);
sun.position.copy(sunDir).multiplyScalar(120);
scene.add(sun);
scene.add(new THREE.HemisphereLight(
  C(P.sky.hemi.sky), C(P.sky.hemi.ground), P.sky.hemi.intensity));

// ---------------------------------------------------------------- 粒子

let particles;
{
  const n = P.particles.count, pos = new Float32Array(n * 3);
  for (let i = 0; i < n * 3; i++) pos[i] = (Math.random() - 0.5) * 60;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  particles = new THREE.Points(g, new THREE.PointsMaterial({
    color: C(P.particles.color), size: P.particles.size,
    transparent: true, opacity: P.particles.opacity, depthWrite: false,
  }));
  scene.add(particles);
}

// ---------------------------------------------------------------- 相机行走

const walker = {
  x: P.walk.x, z: P.walk.startZ,
  speed: 0, targetSpeed: 0,
  yawOff: 0, pitchOff: 0, yawTarget: 0, pitchTarget: 0,
};

window.addEventListener('pointermove', (e) => {
  const nx = (e.clientX / window.innerWidth) * 2 - 1;
  const ny = (e.clientY / window.innerHeight) * 2 - 1;
  walker.yawTarget = -nx * 0.16;
  walker.pitchTarget = -ny * 0.08;
});

const clock = new THREE.Clock();
const lookAt = new THREE.Vector3();

function updateCamera(dt, t) {
  walker.speed += (walker.targetSpeed - walker.speed) * Math.min(dt * 0.5, 1);
  const distToDest = walker.z - (DEST.z + 10);
  if (distToDest < 12) walker.targetSpeed = Math.max(0, walker.targetSpeed * distToDest / 12);
  walker.z -= walker.speed * dt;

  const groundY = heightFn(walker.x, walker.z);
  const bob = Math.sin(t * 1.9) * 0.035 * (walker.speed / 0.6);
  camera.position.set(
    walker.x + Math.sin(t * 0.13) * 0.4,
    groundY + 1.62 + bob,
    walker.z
  );

  walker.yawOff += (walker.yawTarget - walker.yawOff) * Math.min(dt * 1.6, 1);
  walker.pitchOff += (walker.pitchTarget - walker.pitchOff) * Math.min(dt * 1.6, 1);

  const lx = walker.x + (DEST.x - walker.x) * 0.6;
  lookAt.set(lx, camera.position.y + 0.5 + walker.pitchOff * 8, walker.z - 40);
  camera.lookAt(lookAt);
  camera.rotation.y += walker.yawOff;
  camera.rotation.x += walker.pitchOff * 0.5;
}

// ---------------------------------------------------------------- 颗粒噪点

{
  const g = document.getElementById('grain');
  const gs = 140;
  g.width = gs; g.height = gs;
  const gctx = g.getContext('2d');
  function regrain() {
    const img = gctx.createImageData(gs, gs);
    for (let i = 0; i < img.data.length; i += 4) {
      const v = Math.random() * 255;
      img.data[i] = img.data[i+1] = img.data[i+2] = v;
      img.data[i+3] = 255;
    }
    gctx.putImageData(img, 0, 0);
  }
  regrain();
  setInterval(regrain, 90);
  g.style.width = '100vw'; g.style.height = '100vh';
  g.style.imageRendering = 'pixelated';
}

// ---------------------------------------------------------------- 环境音 (WebAudio)

let audio = null;
function startAmbience(cfg) {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  // 共享的棕噪声源
  const len = ctx.sampleRate * 4;
  const buf = ctx.createBuffer(1, len, ctx.sampleRate);
  const data = buf.getChannelData(0);
  let last = 0;
  for (let i = 0; i < len; i++) {
    const white = Math.random() * 2 - 1;
    last = (last + 0.02 * white) / 1.02;
    data[i] = last * 3.5;
  }
  const src = ctx.createBufferSource();
  src.buffer = buf; src.loop = true;

  const master = ctx.createGain();
  master.gain.value = 0;
  master.gain.linearRampToValueAtTime(1, ctx.currentTime + 5);
  master.connect(ctx.destination);

  // 每层：滤波器 + 音量，LFO 可调制频率（风的呼啸）或音量（浪的节奏）
  for (const L of cfg.layers) {
    const filter = ctx.createBiquadFilter();
    filter.type = L.type; filter.frequency.value = L.freq; filter.Q.value = L.q;
    const layerGain = ctx.createGain();
    layerGain.gain.value = L.gain;
    src.connect(filter).connect(layerGain).connect(master);
    if (L.lfo) {
      const lfo = ctx.createOscillator(); lfo.frequency.value = L.lfo.hz;
      const depth = ctx.createGain(); depth.gain.value = L.lfo.depth;
      lfo.connect(depth).connect(
        L.lfo.target === 'gain' ? layerGain.gain : filter.frequency);
      lfo.start();
    }
  }

  src.start();
  audio = { ctx, master, gain: 1, muted: false };
}

const muteBtn = document.getElementById('mute');
muteBtn.addEventListener('click', () => {
  if (!audio) return;
  audio.muted = !audio.muted;
  audio.master.gain.linearRampToValueAtTime(audio.muted ? 0 : audio.gain, audio.ctx.currentTime + 0.6);
  muteBtn.textContent = audio.muted ? '◌' : '◉';
});

// ---------------------------------------------------------------- 灵修流程

const $ = (id) => document.getElementById(id);
const textBox = $('text');
const skipHint = $('skipHint');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function waitStage(ms, minMs = 2000) {
  return new Promise((resolve) => {
    let done = false, canSkip = false;
    const minT = setTimeout(() => { canSkip = true; skipHint.classList.add('show'); }, minMs);
    const fullT = setTimeout(finish, ms);
    function onTap() { if (canSkip) finish(); }
    function finish() {
      if (done) return;
      done = true;
      clearTimeout(minT); clearTimeout(fullT);
      skipHint.classList.remove('show');
      window.removeEventListener('pointerdown', onTap);
      resolve();
    }
    window.addEventListener('pointerdown', onTap);
  });
}

function addLine(html, cls = '') {
  const div = document.createElement('div');
  div.className = 'line ' + cls;
  div.innerHTML = html;
  textBox.appendChild(div);
  requestAnimationFrame(() => requestAnimationFrame(() => div.classList.add('show')));
  return div;
}

async function clearText() {
  textBox.classList.add('fadeout');
  await sleep(1900);
  textBox.innerHTML = '';
  textBox.classList.remove('fadeout');
}

async function breathe(cycles = 3) {
  const box = $('breath'), circle = $('breathCircle'), label = $('breathText');
  box.style.display = 'flex';
  for (let i = 0; i < cycles; i++) {
    label.textContent = '吸 气';
    circle.animate([{ transform: 'scale(1)' }, { transform: 'scale(1.55)' }],
      { duration: 4000, fill: 'forwards', easing: 'ease-in-out' });
    await sleep(4400);
    label.textContent = '缓 缓 呼 气';
    circle.animate([{ transform: 'scale(1.55)' }, { transform: 'scale(1)' }],
      { duration: 6000, fill: 'forwards', easing: 'ease-in-out' });
    await sleep(6400);
  }
  box.style.transition = 'opacity 1.5s';
  box.style.opacity = 0;
  await sleep(1500);
  box.style.display = 'none';
}

// ---------------------------------------------------------------- 答题环节

function runQuiz(quiz) {
  const box = $('quiz'), tag = $('quizTag'), qEl = $('quizQ'),
        opts = $('quizOpts'), fb = $('quizFb');
  box.style.display = 'block';
  let qi = 0;

  return new Promise((resolve) => {
    function next() {
      if (qi >= quiz.length) {
        box.style.opacity = 0;
        setTimeout(() => { box.style.display = 'none'; resolve(); }, 800);
        return;
      }
      const Q = quiz[qi++];
      tag.textContent = Q.tag;
      qEl.textContent = Q.q;
      fb.textContent = '';
      opts.innerHTML = '';
      let settled = false;
      Q.opts.forEach((o) => {
        const btn = document.createElement('button');
        btn.className = 'opt';
        btn.textContent = o.t;
        btn.addEventListener('click', () => {
          if (settled) return;
          if (Q.open) {
            // 开放题：每个选项都是被造就的角度
            settled = true;
            btn.classList.add('ok');
            [...opts.children].forEach(b => { if (b !== btn) b.classList.add('no'); });
            fb.textContent = o.fb;
            setTimeout(next, 4200);
          } else if (o.ok) {
            settled = true;
            btn.classList.add('ok');
            [...opts.children].forEach(b => { if (b !== btn) b.classList.add('no'); });
            fb.textContent = Q.explain;
            setTimeout(next, 3400);
          } else {
            // 答错不惩罚：暗掉该项，给一句指回经文的提示，可继续作答
            btn.classList.add('no', 'shake');
            fb.textContent = Q.hint;
          }
        });
        opts.appendChild(btn);
      });
    }
    box.style.opacity = 1;
    next();
  });
}

// 写入墙的存档（与 wall/index.html 共用 localStorage）——只升不降
function lightWall(target) {
  let s = {};
  try { s = JSON.parse(localStorage.getItem('wall1189')) || {}; } catch (e) {}
  for (const k in target) s[k] = Math.max(s[k] || 0, target[k]);
  localStorage.setItem('wall1189', JSON.stringify(s));
}

async function devotionFlow() {
  const F = P.flow;

  for (const line of F.pre) { addLine(line); await waitStage(5000); }
  await clearText();

  await breathe(3);

  for (const line of F.capsule) { addLine(line, 'capsule'); await waitStage(6800); }
  await clearText();

  for (const line of F.verses) { addLine(line); await waitStage(7200); }
  addLine(F.attribution, 'small');
  await waitStage(9000);
  await clearText();

  addLine(F.stillLine);
  await waitStage(9000);
  await clearText();
  for (let i = 0; i < F.meditation.length; i++) {
    addLine(F.meditation[i]);
    await waitStage(i === F.meditation.length - 1 ? 40000 : 5500, i === F.meditation.length - 1 ? 8000 : 2000);
  }
  await clearText();

  addLine(F.bridge);
  await waitStage(7000);
  await clearText();

  if (F.quiz) await runQuiz(F.quiz);
  if (P.wallTarget) lightWall(P.wallTarget);

  $('closingBig').textContent = F.closingBig;
  $('closingDim').innerHTML = F.closingDim;
  const closing = $('closing');
  closing.style.display = 'flex';
  closing.style.opacity = 0;
  closing.style.transition = 'opacity 2s';
  requestAnimationFrame(() => closing.style.opacity = 1);
  if (P.wallTarget) $('toWall').style.display = 'inline-block';
  await sleep(1200);
  $('tile').classList.add('lit');
}

$('stay').addEventListener('click', () => {
  const closing = $('closing');
  closing.style.opacity = 0;
  setTimeout(() => closing.style.display = 'none', 2000);
});

$('enter').addEventListener('click', () => {
  $('intro').classList.add('hidden');
  startAmbience(P.audio);
  muteBtn.style.display = 'block';
  walker.targetSpeed = P.walk.speed;
  setTimeout(devotionFlow, 2500);
});

// ---------------------------------------------------------------- 主循环

function resize() {
  camera.aspect = window.innerWidth / window.innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(window.innerWidth, window.innerHeight);
}
window.addEventListener('resize', resize);

function tick() {
  const dt = Math.min(clock.getDelta(), 0.1);
  const t = clock.elapsedTime;

  updateCamera(dt, t);

  // 粒子随风漂移，环绕相机回收
  const pp = particles.geometry.attributes.position;
  for (let i = 0; i < pp.count; i++) {
    let x = pp.getX(i) + dt * (P.particles.drift + Math.sin(i) * 0.3);
    let y = pp.getY(i) + dt * Math.sin(t * 0.7 + i) * 0.15;
    if (x > 30) x -= 60;
    pp.setX(i, x); pp.setY(i, y);
  }
  pp.needsUpdate = true;
  particles.position.copy(camera.position);

  // 低多边形水面波动
  if (water) {
    const W = P.water;
    const wp = water.geometry.attributes.position;
    for (let i = 0; i < wp.count; i++) {
      const x = wp.getX(i), z = wp.getZ(i);
      wp.setY(i,
        W.waveAmp * (Math.sin(x * W.waveFreq + t * W.speed)
                   + 0.6 * Math.sin(z * W.waveFreq * 1.3 + t * W.speed * 0.8)
                   + 0.3 * Math.sin((x + z) * W.waveFreq * 0.6 + t * W.speed * 1.4)));
    }
    wp.needsUpdate = true;
    water.geometry.computeVertexNormals();
  }

  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
tick();

setTimeout(() => { document.getElementById('fadeBlack').style.opacity = 0; }, 150);

/* 旷野 · Wilderness —— 沙漠灵修原型
 * 美学参照：低多边形 + 柔和渐变天空 + 胶片颗粒 + 缓慢镜头
 * 零构建，three.js r147 (UMD, 本地)
 */

// ---------------------------------------------------------------- 基础

const canvas = document.getElementById('scene');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.outputEncoding = THREE.sRGBEncoding;

const scene = new THREE.Scene();

const HORIZON = new THREE.Color('#f0c8a2');
const ZENITH  = new THREE.Color('#7d8fb3');
const SUNCOL  = new THREE.Color('#ffe3b8');
const SAND    = new THREE.Color('#d8b88e');

scene.fog = new THREE.Fog(HORIZON.getHex(), 70, 430);

const camera = new THREE.PerspectiveCamera(58, window.innerWidth / window.innerHeight, 0.1, 2000);

// 太阳低垂在正前方偏右的地平线上
const sunDir = new THREE.Vector3(-0.22, 0.10, -1).normalize();

// ---------------------------------------------------------------- 天空

const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide,
  depthWrite: false,
  uniforms: {
    topColor:     { value: ZENITH },
    horizonColor: { value: HORIZON },
    sunColor:     { value: SUNCOL },
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
      float disc = pow(sunDot, 900.0) * 1.4;   // 日轮
      float halo = pow(sunDot, 7.0)   * 0.28;  // 晕
      gl_FragColor = vec4(sky + sunColor * (disc + halo), 1.0);
    }`,
});
scene.add(new THREE.Mesh(new THREE.SphereGeometry(900, 32, 20), skyMat));

// 残星（黎明前，很淡）
{
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
    transparent: true, opacity: 0.35, fog: false, depthWrite: false,
  })));
}

// ---------------------------------------------------------------- 沙丘

// 确定性的丘陵函数（相机行走也用它取高度）
function duneHeight(x, z) {
  let h = 0;
  h += 3.4 * Math.sin(x * 0.021 + Math.sin(z * 0.013) * 1.7);
  h += 2.2 * Math.sin(z * 0.016 + Math.sin(x * 0.011) * 2.3);
  h += 0.9 * Math.sin(x * 0.061 + z * 0.043);
  h += 0.35 * Math.sin(x * 0.13 - z * 0.11);
  // 沿 x≈0 留一条走廊，行走路线平缓
  const corridor = Math.exp(-(x * x) / (2 * 18 * 18));
  return h * (1 - 0.5 * corridor);
}

{
  const geo = new THREE.PlaneGeometry(900, 900, 170, 170);
  geo.rotateX(-Math.PI / 2);
  const p = geo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    p.setY(i, duneHeight(p.getX(i), p.getZ(i)));
  }
  geo.computeVertexNormals();
  const mat = new THREE.MeshStandardMaterial({
    color: SAND, roughness: 1.0, metalness: 0.0, flatShading: true,
  });
  scene.add(new THREE.Mesh(geo, mat));
}

// 零星黑岩
{
  const rockMat = new THREE.MeshStandardMaterial({
    color: 0x5d4a3c, roughness: 1, flatShading: true,
  });
  const spots = [
    [-34, 20], [28, -8], [-52, -46], [45, -70], [-23, -105],
    [60, -140], [-70, -170], [19, -195], [-38, -240], [75, -60],
  ];
  for (const [x, z] of spots) {
    const s = 0.8 + ((x * 7 + z * 13) % 10 + 10) % 10 * 0.22;
    const rock = new THREE.Mesh(new THREE.IcosahedronGeometry(s, 0), rockMat);
    rock.position.set(x, duneHeight(x, z) + s * 0.3, z);
    rock.rotation.set(x, z, x + z);
    rock.scale.y = 0.65;
    scene.add(rock);
  }
}

// 远处一棵孤树（行走的目的地）
const TREE = new THREE.Vector3(7, 0, -150);
TREE.y = duneHeight(TREE.x, TREE.z);
{
  const dark = new THREE.MeshStandardMaterial({ color: 0x4d453a, roughness: 1, flatShading: true });
  const leaf = new THREE.MeshStandardMaterial({ color: 0x5a5c42, roughness: 1, flatShading: true });
  const tree = new THREE.Group();
  const trunk = new THREE.Mesh(new THREE.CylinderGeometry(0.14, 0.3, 3.4, 6), dark);
  trunk.position.y = 1.7;
  trunk.rotation.z = 0.08;
  tree.add(trunk);
  const c1 = new THREE.Mesh(new THREE.ConeGeometry(2.6, 0.9, 7), leaf);
  c1.position.set(0.3, 3.55, 0);
  const c2 = new THREE.Mesh(new THREE.ConeGeometry(1.7, 0.7, 6), leaf);
  c2.position.set(-0.7, 3.1, 0.5);
  tree.add(c1, c2);
  tree.position.copy(TREE);
  scene.add(tree);
}

// ---------------------------------------------------------------- 光

const sun = new THREE.DirectionalLight(0xffd9ae, 1.15);
sun.position.copy(sunDir).multiplyScalar(120);
scene.add(sun);
scene.add(new THREE.HemisphereLight(0x8fa3c4, 0xcaa87e, 0.65));

// ---------------------------------------------------------------- 飘沙粒子

let sandPts;
{
  const n = 320, pos = new Float32Array(n * 3);
  for (let i = 0; i < n * 3; i++) pos[i] = (Math.random() - 0.5) * 60;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  sandPts = new THREE.Points(g, new THREE.PointsMaterial({
    color: 0xe8d0a8, size: 0.05, transparent: true, opacity: 0.55, depthWrite: false,
  }));
  scene.add(sandPts);
}

// ---------------------------------------------------------------- 相机行走

const walker = {
  z: 55,            // 从 z=55 走到树旁
  x: 0,
  speed: 0,          // 进入后升到 0.58 m/s
  targetSpeed: 0,
  yawOff: 0, pitchOff: 0,        // 鼠标视差（平滑后）
  yawTarget: 0, pitchTarget: 0,
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

  // 快到树时缓停
  const distToTree = walker.z - (TREE.z + 10);
  if (distToTree < 12) walker.targetSpeed = Math.max(0, walker.targetSpeed * distToTree / 12);
  walker.z -= walker.speed * dt;

  const groundY = duneHeight(walker.x, walker.z);
  const bob = Math.sin(t * 1.9) * 0.035 * (walker.speed / 0.6);
  camera.position.set(
    walker.x + Math.sin(t * 0.13) * 0.4,
    groundY + 1.62 + bob,
    walker.z
  );

  walker.yawOff += (walker.yawTarget - walker.yawOff) * Math.min(dt * 1.6, 1);
  walker.pitchOff += (walker.pitchTarget - walker.pitchOff) * Math.min(dt * 1.6, 1);

  // 目光落在树与地平线之间
  lookAt.set(TREE.x * 0.6, camera.position.y + 0.5 + walker.pitchOff * 8, walker.z - 40);
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

// ---------------------------------------------------------------- 风声 (WebAudio)

let audio = null;
function startWind() {
  const ctx = new (window.AudioContext || window.webkitAudioContext)();
  // 棕噪声
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

  const lp = ctx.createBiquadFilter();
  lp.type = 'lowpass'; lp.frequency.value = 420; lp.Q.value = 0.4;

  // 慢 LFO 做阵风
  const lfo = ctx.createOscillator(); lfo.frequency.value = 0.06;
  const lfoGain = ctx.createGain(); lfoGain.gain.value = 180;
  lfo.connect(lfoGain).connect(lp.frequency);

  const master = ctx.createGain();
  master.gain.value = 0;
  master.gain.linearRampToValueAtTime(0.22, ctx.currentTime + 5);

  src.connect(lp).connect(master).connect(ctx.destination);
  src.start(); lfo.start();
  audio = { ctx, master, muted: false };
}

const muteBtn = document.getElementById('mute');
muteBtn.addEventListener('click', () => {
  if (!audio) return;
  audio.muted = !audio.muted;
  audio.master.gain.linearRampToValueAtTime(audio.muted ? 0 : 0.22, audio.ctx.currentTime + 0.6);
  muteBtn.textContent = audio.muted ? '◌' : '◉';
});

// ---------------------------------------------------------------- 灵修流程

const $ = (id) => document.getElementById(id);
const textBox = $('text');
const skipHint = $('skipHint');

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

// 等待 ms 毫秒；minMs 之后允许点击跳过
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
    circle.animate(
      [{ transform: 'scale(1)' }, { transform: 'scale(1.55)' }],
      { duration: 4000, fill: 'forwards', easing: 'ease-in-out' });
    await sleep(4400);
    label.textContent = '缓 缓 呼 气';
    circle.animate(
      [{ transform: 'scale(1.55)' }, { transform: 'scale(1)' }],
      { duration: 6000, fill: 'forwards', easing: 'ease-in-out' });
    await sleep(6400);
  }
  box.style.transition = 'opacity 1.5s';
  box.style.opacity = 0;
  await sleep(1500);
  box.style.display = 'none';
}

async function devotionFlow() {
  // 1. 静下来
  addLine('你走了很远的路，来到这里。');
  await waitStage(5200);
  addLine('先让呼吸慢下来。');
  await waitStage(4500);
  await clearText();

  await breathe(3);

  // 2. 上下文胶囊
  addLine('两千七百年前，以色列远离了她的神。', 'capsule');
  await waitStage(7000);
  addLine('神没有用责备把她追回来——', 'capsule');
  await waitStage(6000);
  addLine('祂选择把她带到一个安静的地方。', 'capsule');
  await waitStage(7500);
  await clearText();

  // 3. 经文
  addLine('「看哪，我要劝导她，');
  await waitStage(7000);
  addLine('领她到旷野，');
  await waitStage(7000);
  addLine('在那里，我要对她说安慰的话。」');
  await waitStage(8000);
  addLine('—— 何西阿书 2:14', 'small');
  await waitStage(9000);
  await clearText();

  // 4. 默想（只剩风声）
  addLine('此刻，只有风声。');
  await waitStage(9000);
  await clearText();
  addLine('如果神此刻要对你说一句安慰的话，');
  await waitStage(5500);
  addLine('你觉得，会是哪一句？');
  await waitStage(40000, 8000);
  await clearText();

  addLine('把它放在心里，带出旷野。');
  await waitStage(7000);
  await clearText();

  // 5. 结束
  const closing = $('closing');
  closing.style.display = 'flex';
  closing.style.opacity = 0;
  closing.style.transition = 'opacity 2s';
  requestAnimationFrame(() => closing.style.opacity = 1);
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
  startWind();
  muteBtn.style.display = 'block';
  walker.targetSpeed = 0.58;
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

  // 飘沙：随风向移动并环绕相机回收
  const p = sandPts.geometry.attributes.position;
  for (let i = 0; i < p.count; i++) {
    let x = p.getX(i) + dt * (1.2 + Math.sin(i) * 0.4);
    let y = p.getY(i) + dt * Math.sin(t * 0.7 + i) * 0.15;
    if (x > 30) x -= 60;
    p.setX(i, x); p.setY(i, y);
  }
  p.needsUpdate = true;
  sandPts.position.set(camera.position.x, camera.position.y, camera.position.z);

  renderer.render(scene, camera);
  requestAnimationFrame(tick);
}
tick();

// 开场从黑场淡入
setTimeout(() => {
  document.getElementById('fadeBlack').style.opacity = 0;
}, 150);

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';

const props = defineProps({
  status: { type: String, default: 'idle' },
  intensity: { type: Number, default: 0.0 }
});

const canvasRef = ref(null);
let animationId = null;

// --- CONFIGURACIÓN VISUAL 3D (TOROIDE CON RAYOS) ---
const PARTICLE_COUNT = 300;
const RAY_COUNT = 40; // Naves/Rayos que cruzan
const R_MAJOR = 85;
const R_MINOR_BASE = 18;

const particles = [];
const rays = [];

// Partículas de estructura (puntos estáticos/rotativos)
for (let i = 0; i < PARTICLE_COUNT; i++) {
  particles.push({
    u: Math.random() * Math.PI * 2,
    v: Math.random() * Math.PI * 2,
    speedU: (Math.random() * 0.005) + 0.002,
    speedV: (Math.random() * 0.003) + 0.001,
    hue: Math.random() > 0.5 ? 180 : 210,
    brightness: 40 + Math.random() * 40
  });
}

// Rayos de energía (Naves rápidas)
for (let i = 0; i < RAY_COUNT; i++) {
  rays.push({
    u: Math.random() * Math.PI * 2,
    v: Math.random() * Math.PI * 2,
    speedU: (Math.random() * 0.04) + 0.02, // Mucho más rápidos
    speedV: (Math.random() * 0.02) + 0.01,
    len: 0.2 + Math.random() * 0.3, // Longitud de la estela
    hue: Math.random() * 360, // Color inicial aleatorio
    cycleSpeed: 1 + Math.random() * 2 // Velocidad de cambio de color
  });
}

const draw = () => {
  const canvas = canvasRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  if (canvas.width !== canvas.clientWidth || canvas.height !== canvas.clientHeight) {
    canvas.width = canvas.clientWidth;
    canvas.height = canvas.clientHeight;
  }

  const w = canvas.width;
  const h = canvas.height;
  const cx = w / 2;
  const cy = h / 2;

  ctx.clearRect(0, 0, w, h);

  const isSpeaking = props.status === 'speaking';

  // VIBRACIÓN MÁS SUAVE Y ONDULANTE
  const time = Date.now() * 0.001;
  const shakeSpeed = isSpeaking ? 8 : 0; // Mucho más lento (antes 15) para suavidad
  const shakeAmp = isSpeaking ? props.intensity * 4 : 0; // Amplitud mantenida pero movimiento lento
  const shakeX = Math.sin(time * shakeSpeed) * shakeAmp;
  const shakeY = Math.cos(time * shakeSpeed * 1.1) * shakeAmp;

  // Latido - Aumentado al hablar (antes * 20)
  const audioKick = props.intensity * 35;
  const pulse = isSpeaking ? audioKick : Math.sin(time * 1.5) * 2;
  const currentRMinor = R_MINOR_BASE + pulse;

  const renderList = [];

  // 1. PROCESAR ESTRUCTURA (Puntos suaves)
  particles.forEach(p => {
    const speedMult = isSpeaking ? 1.5 : 0.8;
    p.u += p.speedU * speedMult;
    p.v += p.speedV * speedMult;

    projectPoint(p.u, p.v, currentRMinor, time, shakeX, shakeY, cx, cy, (x, y, scale, z) => {
      renderList.push({
        type: 'dot',
        x, y, scale, z,
        hue: p.hue,
        alpha: Math.min(1, scale - 0.3) * 0.6 // Semi transparentes
      });
    });
  });

  // 2. PROCESAR RAYOS (Líneas finas cambiantes)
  rays.forEach(r => {
    // Velocidad furiosa
    const speedMult = isSpeaking ? 2.0 : 1.2;
    r.u += r.speedU * speedMult;
    r.v += r.speedV * speedMult;

    // Ciclo de color
    r.hue = (r.hue + r.cycleSpeed) % 360;

    // Calculamos inicio y fin del rayo para dibujarlo como línea
    projectPoint(r.u, r.v, currentRMinor, time, shakeX, shakeY, cx, cy, (x1, y1, scale1, z1) => {
      // Punto final (atrás en el tiempo U)
      projectPoint(r.u - r.len, r.v - (r.len * 0.5), currentRMinor, time, shakeX, shakeY, cx, cy, (x2, y2, scale2, z2) => {
        renderList.push({
          type: 'ray',
          x: x1, y: y1, z: z1,
          xEnd: x2, yEnd: y2,
          hue: r.hue,
          scale: scale1,
          alpha: Math.min(1, scale1 - 0.2)
        });
      });
    });
  });

  // Ordenar todo por profundidad
  renderList.sort((a, b) => b.z - a.z);

  // DIBUJAR
  renderList.forEach(item => {
    if (item.alpha <= 0) return;

    if (item.type === 'dot') {
      const glowSize = (isSpeaking ? 5 : 3) * item.scale;

      // Glow muy sutil
      const grad = ctx.createRadialGradient(item.x, item.y, 0, item.x, item.y, glowSize);
      grad.addColorStop(0, `hsla(${item.hue}, 100%, 70%, ${item.alpha})`);
      grad.addColorStop(1, `hsla(${item.hue}, 100%, 50%, 0)`);

      ctx.fillStyle = grad;
      ctx.beginPath();
      ctx.arc(item.x, item.y, glowSize, 0, Math.PI * 2);
      ctx.fill();

      // Punto central
      ctx.fillStyle = `hsla(${item.hue}, 100%, 90%, ${item.alpha})`;
      ctx.beginPath();
      ctx.arc(item.x, item.y, 1.0 * item.scale, 0, Math.PI * 2);
      ctx.fill();
    }
    else if (item.type === 'ray') {
      // DIBUJO DE RAYO "NAVE"
      ctx.beginPath();
      ctx.moveTo(item.x, item.y);
      ctx.lineTo(item.xEnd, item.yEnd);
      ctx.lineCap = 'round';

      // Color brillante y cambiante
      ctx.strokeStyle = `hsla(${item.hue}, 100%, 80%, ${item.alpha})`;
      ctx.lineWidth = 1.5 * item.scale;
      ctx.stroke();

      // Destello en la cabeza del rayo
      ctx.fillStyle = '#fff';
      ctx.beginPath();
      ctx.arc(item.x, item.y, 1.5 * item.scale, 0, Math.PI * 2);
      ctx.fill();
    }
  });

  // Halo Global
  // Base aumentada a 0.20 para que se vea en reposo (petición usuario)
  const haloIntensity = 0.20 + (isSpeaking ? props.intensity * 0.4 : Math.abs(Math.sin(time * 2)) * 0.1);
  const globalGrad = ctx.createRadialGradient(cx, cy, R_MAJOR * 0.5, cx, cy, R_MAJOR * 2.0);
  globalGrad.addColorStop(0, 'rgba(0,0,0,0)');
  globalGrad.addColorStop(0.4, `rgba(34, 211, 238, ${haloIntensity * 0.4})`);
  globalGrad.addColorStop(1, 'rgba(0,0,0,0)');

  ctx.globalCompositeOperation = 'destination-over';
  ctx.fillStyle = globalGrad;
  ctx.fillRect(0, 0, w, h);
  ctx.globalCompositeOperation = 'source-over';

  animationId = requestAnimationFrame(draw);
};

// Función auxiliar de proyección 3D del Toroide
function projectPoint(u, v, rMinor, time, shakeX, shakeY, cx, cy, callback) {
  let x3d = (R_MAJOR + rMinor * Math.cos(u)) * Math.cos(v);
  let y3d = (R_MAJOR + rMinor * Math.cos(u)) * Math.sin(v);
  let z3d = rMinor * Math.sin(u);

  // Rotación de Cámara
  const rotX = 1.1;
  let yRot = y3d * Math.cos(rotX) - z3d * Math.sin(rotX);
  let zRot = y3d * Math.sin(rotX) + z3d * Math.cos(rotX);

  // Giro constante
  const rotZ = time * 0.3;
  let xFinal = x3d * Math.cos(rotZ) - yRot * Math.sin(rotZ);
  let yFinal = x3d * Math.sin(rotZ) + yRot * Math.cos(rotZ);
  let zFinal = zRot;

  const fov = 400;
  const scale = fov / (fov + zFinal);

  callback(
    cx + xFinal * scale + shakeX,
    cy + yFinal * scale + shakeY,
    scale,
    zFinal
  );
}

onMounted(() => {
  animationId = requestAnimationFrame(draw);
});

onUnmounted(() => {
  if (animationId) cancelAnimationFrame(animationId);
});
</script>

<template>
  <div class="fina-torus-container">
    <canvas ref="canvasRef" class="w-full h-full"></canvas>
  </div>
</template>

<style scoped>
.fina-torus-container {
  width: 400px;
  height: 400px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>

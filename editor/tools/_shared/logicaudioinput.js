// Per-node audio analysers. Devices share one microphone stream; asset nodes
// decode only their own URL and never request microphone permission.
import { LogicPermission } from './logicpermission.js';
function clamp(v, lo, hi) { return Math.min(hi, Math.max(lo, v)); }
function num(v, fallback) { return Number.isFinite(Number(v)) ? Number(v) : fallback; }

export function createAudioInputs(nodes) {
  let ctx=null, micStream=null, disposed=false, requested=null;
  const records={}, players=[];
  const configs=(nodes||[]).map(n=>({id:n.id,params:n.params||{}}));
  function sampler(p, source, audible) {
    const audioCtx=ctx, audio={level:0,pitch:0,band:0,raw:0,beat:false};
    const analyser=ctx.createAnalyser();
    analyser.fftSize=Math.pow(2,Math.round(Math.log2(clamp(num(p.fftSize,2048),32,32768))));
    analyser.smoothingTimeConstant=clamp(num(p.smoothing,0.8),0,1);
    const freqBuf=new Uint8Array(analyser.frequencyBinCount),timeBuf=new Uint8Array(analyser.fftSize);
    const audioCfg={band:p.band||'full'};
    let beatPrevLevel=0,pitchFrame=0;
    source.connect(analyser);
    const gain=ctx.createGain();gain.gain.value=audible?1:0;analyser.connect(gain);gain.connect(ctx.destination);
    const sampleAudio=()=>{
      analyser.getByteFrequencyData(freqBuf);
      analyser.getByteTimeDomainData(timeBuf);
      // RMS loudness 0..1 from the time-domain waveform.
      let sum = 0;
      for (let i = 0; i < timeBuf.length; i++) { const v = (timeBuf[i] - 128) / 128; sum += v * v; }
      const level = Math.sqrt(sum / timeBuf.length);
      audio.raw = level;
      audio.level = clamp(level * 1.8, 0, 1);  // gentle gain so quiet rooms still read
      // Band energy (averaged frequency bins for the selected band).
      const N = freqBuf.length;
      let lo = 0, hi = N;
      if (audioCfg.band === 'bass') { lo = 0; hi = Math.floor(N * 0.08); }
      else if (audioCfg.band === 'mid') { lo = Math.floor(N * 0.08); hi = Math.floor(N * 0.4); }
      else if (audioCfg.band === 'treble') { lo = Math.floor(N * 0.4); hi = N; }
      let bsum = 0, bcount = 0;
      for (let i = lo; i < hi; i++) { bsum += freqBuf[i]; bcount++; }
      audio.band = bcount ? clamp((bsum / bcount) / 255, 0, 1) : 0;
      // Full spectrum (64 bins) + 16 log-spaced band energies, normalized 0..1,
      // exposed as channels. Buffers are reused across frames (no per-frame alloc).
      const SB = 64, LB = 16;
      if (!audio.spectrum) audio.spectrum = new Float32Array(SB);
      for (let k = 0; k < SB; k++) {
        const a0 = Math.floor(k * N / SB), a1 = Math.max(a0 + 1, Math.floor((k + 1) * N / SB));
        let s = 0; for (let i = a0; i < a1; i++) s += freqBuf[i];
        audio.spectrum[k] = (s / (a1 - a0)) / 255;
      }
      if (!audio.bands) audio.bands = new Float32Array(LB);
      for (let k = 0; k < LB; k++) {
        const f0 = Math.floor(N * Math.pow(k / LB, 2)), f1 = Math.max(f0 + 1, Math.floor(N * Math.pow((k + 1) / LB, 2)));
        let s = 0; for (let i = f0; i < f1; i++) s += freqBuf[i];
        audio.bands[k] = (s / (f1 - f0)) / 255;
      }
      // Autocorrelation pitch estimate (Hz) from the time-domain buffer. The
      // ACF is by far the most expensive extraction here, and the consumer
      // contract forces a read every frame (logicgraph's input-audio evaluator
      // resolves ALL out-ports each tick, pitch included, so a lazy getter
      // would be forced anyway) - so recompute only every AC_EVERY frames;
      // voice pitch moves slowly relative to the frame rate and the last
      // value holds in between.
      if ((pitchFrame++ % AC_EVERY) === 0) {
        audio.pitch = audioCtx ? autoCorrelate(timeBuf, audioCtx.sampleRate) : 0;
      }
      // Beat = a sharp rise in level above the running floor.
      audio.beat = (audio.level - beatPrevLevel) > 0.12 && audio.level > 0.15;
      beatPrevLevel = beatPrevLevel * 0.86 + audio.level * 0.14;
    };

    return ()=>{sampleAudio();return {...audio};};
  }
  function request() {
    if(disposed)return Promise.resolve(false);
    if(requested)return requested;
    const needsMic=configs.some(n=>n.params.source!=='asset');
    requested=LogicPermission.requestGesture({title:needsMic?'Enable audio input':'Play audio asset',
      body:needsMic?'This piece uses your microphone. Your browser will ask for access.':'This piece plays the connected audio and reacts to its sound.',
      allowLabel:needsMic?'Enable microphone':'Play sound'},async()=>{
      if(disposed)return false;
      const AC=window.AudioContext||window.webkitAudioContext;
      ctx=new AC(); await ctx.resume();
      if(needsMic){
        micStream=await navigator.mediaDevices.getUserMedia({audio:true});
        if(disposed){micStream.getTracks().forEach(t=>t.stop());return false;}
      }
      await Promise.all(configs.map(async n=>{
        if(disposed)return;
        const p=n.params;
        if(p.source==='asset'){
          if(!p._assetUrl)throw new Error('Audio asset is not connected');
          const response=await fetch(p._assetUrl);
          if(!response.ok)throw new Error('Audio asset HTTP '+response.status);
          const buffer=await ctx.decodeAudioData(await response.arrayBuffer());
          if(disposed)return;
          const player=ctx.createBufferSource();player.buffer=buffer;player.loop=true;
          records[n.id]=sampler(p,player,true);players.push(player);player.start();
        }else{
          records[n.id]=sampler(p,ctx.createMediaStreamSource(micStream),false);
        }
      }));
      return true;
    }).then(value=>{if(!value)api.dispose();return !!value;}).catch(error=>{ api.error=String(error.message||error); api.dispose(); return false; });
    return requested;
  }
  const api={request,error:null,
    sample(){const out={};for(const [id,sample] of Object.entries(records))out[id]=sample();return out;},
    dispose(){disposed=true;for(const p of players){try{p.stop();}catch(_){}}if(micStream)micStream.getTracks().forEach(t=>t.stop());if(ctx)ctx.close();}
  };
  return api;
}

const AC_WINDOW = 512;
const AC_EVERY = 3;
let acSignal = null;                          // Float32Array(fftSize), lazily sized
const acCorr = new Float32Array(AC_WINDOW);   // ACF accumulator, fixed cap
function autoCorrelate(buf, sampleRate) {
  const SIZE = buf.length;
  if (!acSignal || acSignal.length !== SIZE) acSignal = new Float32Array(SIZE);
  const f = acSignal;
  let rms = 0;
  for (let i = 0; i < SIZE; i++) { f[i] = (buf[i] - 128) / 128; rms += f[i] * f[i]; }
  rms = Math.sqrt(rms / SIZE);
  if (rms < 0.01) return 0;  // too quiet to estimate

  let r1 = 0, r2 = SIZE - 1; const thres = 0.2;
  for (let i = 0; i < SIZE / 2; i++) { if (Math.abs(f[i]) < thres) { r1 = i; break; } }
  for (let i = 1; i < SIZE / 2; i++) { if (Math.abs(f[SIZE - i]) < thres) { r2 = SIZE - i; break; } }
  const n = Math.min(r2 - r1, AC_WINDOW);
  if (n < 2) return 0;

  // ACF over the trimmed window, indexed in place (no slice; the lag in
  // samples is what sets the period, so sampleRate / T0 below is unchanged).
  const c = acCorr;
  for (let lag = 0; lag < n; lag++) {
    let s = 0;
    for (let i = 0; i < n - lag; i++) s += f[r1 + i] * f[r1 + i + lag];
    c[lag] = s;
  }
  let d = 0; while (d < n - 1 && c[d] > c[d + 1]) d++;
  let maxVal = -1, maxPos = -1;
  for (let i = d; i < n; i++) { if (c[i] > maxVal) { maxVal = c[i]; maxPos = i; } }
  if (maxPos <= 0) return 0;
  // Parabolic interpolation around the peak for sub-sample accuracy. c is a
  // fixed-size scratch, so entries at n and beyond are stale - guard the +1.
  let T0 = maxPos;
  const x1 = c[maxPos - 1] || 0, x2 = c[maxPos], x3 = (maxPos + 1 < n ? c[maxPos + 1] : 0);
  const a = (x1 + x3 - 2 * x2) / 2, b = (x3 - x1) / 2;
  if (a) T0 = maxPos - b / (2 * a);
  return T0 > 0 ? sampleRate / T0 : 0;
}

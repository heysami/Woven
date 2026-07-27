/* woven-voice.js - runtime voice helper for Woven prototypes.
 *
 * Gives a built prototype dynamic speech (TTS on text computed at runtime)
 * and voice input (mic capture -> transcript), with graceful fallback tiers:
 *
 *   speak: ElevenLabs via the Woven daemon  ->  browser speechSynthesis  ->  silent {ok:false}
 *   listen: daemon STT (whisper)            ->  browser SpeechRecognition ->  {ok:false}
 *
 * Ship it as a BAKED sibling file (source/<slug>/woven-voice.js) next to the
 * prototype HTML with <script src="woven-voice.js"></script> - that way the
 * same file works served by the local daemon, through a share tunnel, and on
 * a hosted (R2 snapshot) share. The helper resolves its endpoint base from
 * the page URL: share paths (/s/<token>/...) use the gate's
 * /s/<token>/api/voice/* routes; everything else uses the daemon's /__voice/*.
 *
 * Rules baked in (do not fight them):
 *   - the first audible speak happens only after a user gesture (autoplay
 *     policy); earlier speak() calls queue and flush on the first gesture.
 *   - getUserMedia is requested only inside listen()/listenStart(), never at
 *     load time.
 *   - all failures downgrade quietly; nothing throws for a missing backend.
 *
 * API:
 *   WovenVoice.probe()                 -> Promise<{tts, stt}>  tiers: 'cloud'|'daemon'|'browser'|'none'
 *   WovenVoice.speak(text, opts?)      -> Promise<{ok, engine, cached?}> resolves AFTER playback ends
 *        opts: { voiceId, modelId, voiceSettings, interrupt, coalesceKey, volume, rate }
 *   WovenVoice.stop()                  -> cancel current + queued utterances
 *   WovenVoice.listen(opts?)           -> Promise<{ok, text, engine}>  (opts: {maxMs})
 *   WovenVoice.listenStart() / WovenVoice.listenStop()  -> push-to-talk pair
 *   WovenVoice.setMuted(bool) / WovenVoice.setVolume(0..1)
 *   WovenVoice.voices()                -> Promise<[{id,name,character,castFor}]>
 *   WovenVoice.on(evt, fn)             -> evt: speakstart|speakend|listenstart|listenend|fallback|error
 */
(function () {
  "use strict";
  if (window.WovenVoice) return;

  // ── endpoint base ─────────────────────────────────────────────────────────
  var shareMatch = location.pathname.match(/^(\/s\/[a-f0-9]{24,64})\//);
  var BASE = shareMatch ? shareMatch[1] + "/api/voice" : "/__voice";

  // ── state ─────────────────────────────────────────────────────────────────
  var muted = false;
  var volume = 1.0;
  var probed = null;          // {tts, stt} or null
  var probedAt = 0;
  var unlocked = false;       // autoplay unlock happened
  var queue = [];             // [{text, opts, resolve}]
  var speaking = false;
  var currentAudio = null;    // the ONE shared <audio> element (Safari autoplay)
  var currentUtterance = null;
  var listeners = {};
  var recorder = null;
  var recorderStream = null;
  var recorderChunks = null;
  var recorderResolve = null;
  var recorderTimer = null;

  function emit(evt, detail) {
    var fns = listeners[evt] || [];
    for (var i = 0; i < fns.length; i++) {
      try { fns[i](detail || {}); } catch (e) { /* listener errors never break the pipeline */ }
    }
    try { console.log("[woven-voice] " + evt, detail || ""); } catch (e) {}
  }

  function audioEl() {
    if (!currentAudio) {
      currentAudio = new Audio();
      currentAudio.preload = "auto";
    }
    return currentAudio;
  }

  // ── autoplay unlock: one capture-phase gesture listener ───────────────────
  function unlock() {
    if (unlocked) return;
    unlocked = true;
    var a = audioEl();
    // 0.05s of silence as a data URI - unlocks the shared element for later
    // programmatic play() calls on strict (Safari) autoplay policies.
    a.src = "data:audio/mpeg;base64,//uQxAAAAAAAAAAAAAAAAAAAAAAAWGluZwAAAA8AAAACAAACcQCA" +
            "gICAgICAgICAgICAgICAgICAgICAgP//////////////////////////AAAAAExhdmM1OC4xMwAAAAAAAAAAAAAAACQCkAAAAAAAAAJx" +
            "TgeYYAAAAAAAAAAAAAAAAAAAAP/7kMQAA8AAAaQAAAAgAAA0gAAABExBTUUzLjEwMFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV";
    var p = a.play();
    if (p && p.catch) p.catch(function () {});
    document.removeEventListener("pointerdown", unlock, true);
    document.removeEventListener("keydown", unlock, true);
    pump();
  }
  document.addEventListener("pointerdown", unlock, true);
  document.addEventListener("keydown", unlock, true);

  // ── probe ─────────────────────────────────────────────────────────────────
  function fetchJson(url, opts, timeoutMs) {
    return new Promise(function (resolve, reject) {
      var ctl = ("AbortController" in window) ? new AbortController() : null;
      var timer = setTimeout(function () {
        if (ctl) ctl.abort();
        reject(new Error("timeout"));
      }, timeoutMs || 8000);
      var o = opts || {};
      if (ctl) o.signal = ctl.signal;
      fetch(url, o).then(function (r) {
        clearTimeout(timer);
        if (!r.ok) { reject(new Error("http " + r.status)); return; }
        resolve(r.json());
      }, function (e) { clearTimeout(timer); reject(e); });
    });
  }

  function probe() {
    var now = Date.now();
    if (probed && now - probedAt < 60000) return Promise.resolve(probed);
    return fetchJson(BASE + "/status", { method: "GET" }, 1500).then(function (j) {
      probed = {
        tts: j && j.tts ? "cloud" : (("speechSynthesis" in window) ? "browser" : "none"),
        stt: (j && j.stt && j.stt !== "none") ? "daemon"
             : ((window.SpeechRecognition || window.webkitSpeechRecognition) ? "browser" : "none"),
        defaultVoiceId: j && j.defaultVoiceId,
      };
      probedAt = now;
      return probed;
    }).catch(function () {
      probed = {
        tts: ("speechSynthesis" in window) ? "browser" : "none",
        stt: (window.SpeechRecognition || window.webkitSpeechRecognition) ? "browser" : "none",
      };
      probedAt = now;
      return probed;
    });
  }

  // ── speak ─────────────────────────────────────────────────────────────────
  function speak(text, opts) {
    opts = opts || {};
    text = String(text == null ? "" : text).trim();
    if (!text) return Promise.resolve({ ok: false, engine: "none" });
    if (opts.interrupt) stop();
    return new Promise(function (resolve) {
      if (opts.coalesceKey) {
        // Rapid state changes: replace the not-yet-spoken utterance that
        // carries the same key instead of stacking narration.
        for (var i = queue.length - 1; i >= 0; i--) {
          if (queue[i].opts.coalesceKey === opts.coalesceKey) {
            queue[i].resolve({ ok: false, engine: "coalesced" });
            queue.splice(i, 1);
          }
        }
      }
      queue.push({ text: text, opts: opts, resolve: resolve });
      pump();
    });
  }

  // A stalled utterance must never wedge the queue. Both playback paths end on
  // an event (`ended` / `onend`), and both events are known to go missing in the
  // real world: a machine with no audio device, a backgrounded tab, or the
  // long-standing speechSynthesis stall on long strings. Without this watchdog
  // one missing event means `speaking` stays true forever, every later speak()
  // promise never settles, and any UI awaiting one hangs with it.
  function withWatchdog(promise, text) {
    var budgetMs = Math.max(8000, String(text || "").length * 250);
    return new Promise(function (resolve) {
      var done = false;
      var timer = setTimeout(function () {
        if (done) return;
        done = true;
        try { if ("speechSynthesis" in window) window.speechSynthesis.cancel(); } catch (e) {}
        resolve({ ok: false, engine: "timeout" });
      }, budgetMs);
      promise.then(function (res) {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve(res);
      }, function () {
        if (done) return;
        done = true;
        clearTimeout(timer);
        resolve({ ok: false, engine: "none" });
      });
    });
  }

  function pump() {
    if (speaking || queue.length === 0) return;
    if (!unlocked) return; // parked until the first user gesture
    var item = queue.shift();
    speaking = true;
    var play = playCloud(item).catch(function () {
      return playBrowser(item);
    });
    withWatchdog(play, item.text).then(function (res) {
      speaking = false;
      item.resolve(res || { ok: false, engine: "none" });
      emit("speakend", { text: item.text, engine: res && res.engine });
      pump();
    });
  }

  function playCloud(item) {
    return probe().then(function (p) {
      if (muted) return { ok: false, engine: "muted" };
      if (p.tts !== "cloud") return Promise.reject(new Error("no cloud tts"));
      var body = { text: item.text };
      if (item.opts.voiceId) body.voice_id = item.opts.voiceId;
      if (item.opts.modelId) body.model_id = item.opts.modelId;
      if (item.opts.voiceSettings) body.voice_settings = item.opts.voiceSettings;
      return fetch(BASE + "/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }).then(function (r) {
        if (!r.ok) throw new Error("tts http " + r.status);
        var cached = r.headers.get("X-Voice-Cache") === "hit";
        return r.blob().then(function (blob) {
          return new Promise(function (resolve, reject) {
            var a = audioEl();
            var url = URL.createObjectURL(blob);
            var done = false;
            function finish(ok) {
              if (done) return;
              done = true;
              URL.revokeObjectURL(url);
              a.onended = a.onerror = null;
              if (ok) resolve({ ok: true, engine: "elevenlabs", cached: cached });
              else reject(new Error("playback failed"));
            }
            a.onended = function () { finish(true); };
            a.onerror = function () { finish(false); };
            a.src = url;
            a.volume = (item.opts.volume != null ? item.opts.volume : volume);
            if (item.opts.rate != null) a.playbackRate = item.opts.rate;
            emit("speakstart", { text: item.text, engine: "elevenlabs" });
            var pr = a.play();
            if (pr && pr.catch) pr.catch(function () { finish(false); });
          });
        });
      });
    });
  }

  var fallbackAnnounced = false;
  function playBrowser(item) {
    return new Promise(function (resolve) {
      if (muted || !("speechSynthesis" in window)) {
        resolve({ ok: false, engine: "none" });
        return;
      }
      if (!fallbackAnnounced) {
        fallbackAnnounced = true;
        emit("fallback", { from: "elevenlabs", to: "speechSynthesis" });
      }
      var u = new SpeechSynthesisUtterance(item.text);
      currentUtterance = u;
      u.volume = (item.opts.volume != null ? item.opts.volume : volume);
      if (item.opts.rate != null) u.rate = item.opts.rate;
      var vs = window.speechSynthesis.getVoices() || [];
      for (var i = 0; i < vs.length; i++) {
        // Prefer a natural remote voice matching the page language.
        if (!vs[i].localService && vs[i].lang &&
            vs[i].lang.slice(0, 2) === (document.documentElement.lang || "en").slice(0, 2)) {
          u.voice = vs[i];
          break;
        }
      }
      u.onend = function () { currentUtterance = null; resolve({ ok: true, engine: "speechSynthesis" }); };
      u.onerror = function () { currentUtterance = null; resolve({ ok: false, engine: "speechSynthesis" }); };
      emit("speakstart", { text: item.text, engine: "speechSynthesis" });
      window.speechSynthesis.speak(u);
    });
  }

  function stop() {
    while (queue.length) queue.shift().resolve({ ok: false, engine: "stopped" });
    if (currentAudio && !currentAudio.paused) {
      try { currentAudio.pause(); currentAudio.currentTime = 0; } catch (e) {}
    }
    if ("speechSynthesis" in window) {
      try { window.speechSynthesis.cancel(); } catch (e) {}
    }
    currentUtterance = null;
    speaking = false;
  }

  // ── listen ────────────────────────────────────────────────────────────────
  function pickRecorderMime() {
    if (!window.MediaRecorder) return null;
    var cands = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4"];
    for (var i = 0; i < cands.length; i++) {
      try {
        if (MediaRecorder.isTypeSupported(cands[i])) return cands[i];
      } catch (e) {}
    }
    return ""; // browser default (Safari -> mp4/aac; the daemon's ffmpeg decodes it)
  }

  function listenStart() {
    if (recorder) return Promise.reject(new Error("already listening"));
    return probe().then(function (p) {
      if (p.stt === "daemon" && navigator.mediaDevices && window.MediaRecorder) {
        return navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
          recorderStream = stream;
          recorderChunks = [];
          var mime = pickRecorderMime();
          recorder = mime ? new MediaRecorder(stream, { mimeType: mime }) : new MediaRecorder(stream);
          recorder.ondataavailable = function (e) { if (e.data && e.data.size) recorderChunks.push(e.data); };
          recorder.start();
          emit("listenstart", { engine: "daemon" });
          return { ok: true };
        });
      }
      return Promise.reject(new Error("no daemon stt"));
    });
  }

  function listenStop() {
    return new Promise(function (resolve) {
      if (!recorder) { resolve({ ok: false, text: "", engine: "none" }); return; }
      var rec = recorder;
      var stream = recorderStream;
      var chunks = recorderChunks;
      recorder = null; recorderStream = null; recorderChunks = null;
      if (recorderTimer) { clearTimeout(recorderTimer); recorderTimer = null; }
      rec.onstop = function () {
        try { stream.getTracks().forEach(function (t) { t.stop(); }); } catch (e) {}
        var mime = rec.mimeType || "audio/webm";
        var blob = new Blob(chunks, { type: mime });
        fetch(BASE + "/stt", { method: "POST", headers: { "Content-Type": mime }, body: blob })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            emit("listenend", { engine: j && j.engine, ok: !!(j && j.ok) });
            resolve({ ok: !!(j && j.ok), text: (j && j.text) || "", engine: (j && j.engine) || "daemon" });
          })
          .catch(function (e) {
            emit("error", { where: "stt", message: String(e && e.message || e) });
            resolve({ ok: false, text: "", engine: "daemon" });
          });
      };
      try { rec.stop(); } catch (e) { rec.onstop(); }
    });
  }

  function listenBrowser(maxMs) {
    return new Promise(function (resolve) {
      var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (!SR) { resolve({ ok: false, text: "", engine: "none" }); return; }
      if (!fallbackAnnounced) {
        fallbackAnnounced = true;
        emit("fallback", { from: "daemon-stt", to: "SpeechRecognition" });
      }
      var r = new SR();
      r.continuous = false;
      r.interimResults = false;
      var timer = setTimeout(function () { try { r.stop(); } catch (e) {} }, maxMs || 15000);
      emit("listenstart", { engine: "SpeechRecognition" });
      r.onresult = function (e) {
        clearTimeout(timer);
        var text = "";
        try { text = e.results[0][0].transcript; } catch (err) {}
        emit("listenend", { engine: "SpeechRecognition", ok: !!text });
        resolve({ ok: !!text, text: text, engine: "SpeechRecognition" });
      };
      r.onerror = function () {
        clearTimeout(timer);
        emit("listenend", { engine: "SpeechRecognition", ok: false });
        resolve({ ok: false, text: "", engine: "SpeechRecognition" });
      };
      try { r.start(); } catch (e) { resolve({ ok: false, text: "", engine: "SpeechRecognition" }); }
    });
  }

  function listen(opts) {
    opts = opts || {};
    var maxMs = opts.maxMs || 15000;
    return listenStart().then(function () {
      return new Promise(function (resolve) {
        recorderTimer = setTimeout(function () { listenStop().then(resolve); }, maxMs);
        // Expose an early stop for push-to-talk built on listen():
        listen._stop = function () {
          clearTimeout(recorderTimer);
          recorderTimer = null;
          return listenStop().then(resolve);
        };
      });
    }).catch(function () {
      return listenBrowser(maxMs);
    });
  }

  // ── public API ────────────────────────────────────────────────────────────
  window.WovenVoice = {
    version: "1",
    base: BASE,
    probe: probe,
    speak: speak,
    stop: stop,
    listen: listen,
    listenStart: listenStart,
    listenStop: listenStop,
    setMuted: function (b) { muted = !!b; if (muted) stop(); },
    isMuted: function () { return muted; },
    setVolume: function (v) { volume = Math.max(0, Math.min(1, Number(v) || 0)); },
    voices: function () {
      return fetchJson(BASE + "/voices", { method: "GET" }, 4000)
        .then(function (j) { return (j && j.voices) || []; })
        .catch(function () { return []; });
    },
    on: function (evt, fn) {
      (listeners[evt] = listeners[evt] || []).push(fn);
      return function () {
        var a = listeners[evt] || [];
        var i = a.indexOf(fn);
        if (i >= 0) a.splice(i, 1);
      };
    },
  };
})();

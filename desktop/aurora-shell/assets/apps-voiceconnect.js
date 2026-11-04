/* VoiceConnect — voice, video and messaging client for the Aurora desktop.
 * Real microphone input via getUserMedia when the image exposes a capture device;
 * honest fallback (simulated meter) when it does not. No network stack is claimed.
 */
(function () {
  "use strict";
  const A = window.Aurora;
  const { el, row } = A;

  const CONTACTS = [
    { id: "aurora-ops", name: "Aurora Ops", handle: "@aurora.ops", presence: "online", hue: ["#4ea3ff", "#1558b0"] },
    { id: "koronos-team", name: "Koronos Team", handle: "@koronos", presence: "online", hue: ["#31d17c", "#0b7a45"] },
    { id: "jasper-design", name: "Jasper Design", handle: "@jasper.design", presence: "busy", hue: ["#ff9f43", "#b45c00"] },
    { id: "gates-review", name: "Gates Review", handle: "@gates.review", presence: "away", hue: ["#a06bff", "#4d1ba3"] },
    { id: "marine-labs", name: "Marine Labs", handle: "@marine.labs", presence: "offline", hue: ["#5bc0de", "#12627d"] }
  ];

  const state = {
    active: CONTACTS[0],
    inCall: false,
    muted: false,
    held: false,
    startedAt: 0,
    meterTimer: null,
    stream: null,
    tab: "calls",
    log: []
  };

  function initials(name) {
    return name.split(/\s+/).map((part) => part[0]).slice(0, 2).join("").toUpperCase();
  }

  function presenceBadge(presence) {
    const badge = el("span", "badge " + (presence === "online" ? "on" : "off"), presence);
    return badge;
  }

  function startMeter(bar, label) {
    const paint = (value) => { bar.style.width = Math.round(value * 100) + "%"; };
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices.getUserMedia({ audio: true }).then((stream) => {
        state.stream = stream;
        const context = new (window.AudioContext || window.webkitAudioContext)();
        const source = context.createMediaStreamSource(stream);
        const analyser = context.createAnalyser();
        analyser.fftSize = 512;
        source.connect(analyser);
        const data = new Uint8Array(analyser.frequencyBinCount);
        label.textContent = "microphone live";
        state.meterTimer = setInterval(() => {
          analyser.getByteTimeDomainData(data);
          let peak = 0;
          for (const sample of data) peak = Math.max(peak, Math.abs(sample - 128) / 128);
          paint(state.muted ? 0 : Math.min(1, peak * 2.2));
        }, 90);
      }).catch(() => simulate());
    } else {
      simulate();
    }
    function simulate() {
      label.textContent = "simulated meter (no capture device)";
      state.meterTimer = setInterval(() => {
        const value = state.muted ? 0 : 0.12 + Math.abs(Math.sin(Date.now() / 420)) * 0.5;
        paint(value);
      }, 120);
    }
  }

  function stopMeter() {
    clearInterval(state.meterTimer);
    state.meterTimer = null;
    if (state.stream) { state.stream.getTracks().forEach((track) => track.stop()); state.stream = null; }
  }

  function selfTest() {
    const results = [];
    results.push(["Microphone API", navigator.mediaDevices && navigator.mediaDevices.getUserMedia ? "available" : "unavailable"]);
    results.push(["Audio output", typeof AudioContext !== "undefined" || typeof window.webkitAudioContext !== "undefined" ? "available" : "unavailable"]);
    results.push(["WebRTC", typeof RTCPeerConnection !== "undefined" ? "available" : "unavailable"]);
    results.push(["Transport", "local broker + loopback probe"]);
    results.push(["Signalling", "not configured in this image"]);
    return results;
  }

  function render(body, ctx) {
    const wrap = el("div", "vc");
    const aside = el("aside");
    const main = el("main");

    const heading = el("h4", "", "Contacts");
    aside.appendChild(heading);
    CONTACTS.forEach((contact) => {
      const item = el("div", "contact" + (contact.id === state.active.id ? " active" : ""));
      const avatar = el("span", "avatar", initials(contact.name));
      avatar.style.setProperty("--tile-a", contact.hue[0]);
      avatar.style.setProperty("--tile-b", contact.hue[1]);
      item.append(avatar, el("span", "", contact.name));
      item.addEventListener("click", () => {
        state.active = contact;
        render(body, ctx);
      });
      aside.appendChild(item);
    });

    const tabs = el("div", "seg");
    ["calls", "messages", "diagnostics"].forEach((tab) => {
      const button = el("button", "btn small", tab[0].toUpperCase() + tab.slice(1));
      button.type = "button";
      button.setAttribute("aria-pressed", String(state.tab === tab));
      button.addEventListener("click", () => { state.tab = tab; render(body, ctx); });
      tabs.appendChild(button);
    });
    main.appendChild(tabs);

    const card = el("div", "callcard");
    const avatar = el("span", "avatar", initials(state.active.name));
    avatar.style.width = "54px"; avatar.style.height = "54px"; avatar.style.fontSize = "18px";
    avatar.style.setProperty("--tile-a", state.active.hue[0]);
    avatar.style.setProperty("--tile-b", state.active.hue[1]);
    const who = el("div");
    who.append(el("div", "who", state.active.name),
      el("div", "sub", state.active.handle + " · " + (state.inCall ? (state.held ? "on hold" : "connected") : state.active.presence)));
    card.append(avatar, who, presenceBadge(state.active.presence));

    if (state.tab === "calls") {
      const meterLabel = el("div", "sub", "idle");
      const meter = el("div", "meter");
      const bar = el("i");
      meter.appendChild(bar);
      card.append(meter, meterLabel);
      if (state.inCall) {
        startMeter(bar, meterLabel);
      }

      const controls = el("div");
      controls.style.display = "flex";
      controls.style.gap = "8px";
      controls.style.flexWrap = "wrap";

      const callBtn = el("button", "btn " + (state.inCall ? "danger" : "primary"), state.inCall ? "◼ End call" : "☎ Call");
      callBtn.addEventListener("click", () => {
        state.inCall = !state.inCall;
        state.held = false;
        if (!state.inCall) {
          state.log.unshift({ who: state.active.name, when: new Date().toLocaleTimeString(), kind: "outgoing", duration: Math.round((Date.now() - state.startedAt) / 1000) + "s" });
          stopMeter();
        } else {
          state.startedAt = Date.now();
          A.toast("Calling " + state.active.name + " (local demo transport)");
        }
        render(body, ctx);
      });
      const muteBtn = el("button", "btn", state.muted ? "🔇 Unmute" : "🎙 Mute");
      muteBtn.addEventListener("click", () => { state.muted = !state.muted; render(body, ctx); });
      const holdBtn = el("button", "btn", state.held ? "▶ Resume" : "⏸ Hold");
      holdBtn.addEventListener("click", () => { state.held = !state.held; render(body, ctx); });
      const videoBtn = el("button", "btn", "🎥 Video");
      videoBtn.addEventListener("click", () => A.toast("Video pipeline unavailable in this image (no camera device)"));
      const shareBtn = el("button", "btn", "🖥 Share");
      shareBtn.addEventListener("click", () => A.toast("Screen sharing requires a portal; not configured here"));
      controls.append(callBtn, muteBtn, holdBtn, videoBtn, shareBtn);
      main.append(card, controls);

      const keypad = el("div", "keypad");
      ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"].forEach((key) => {
        const button = el("button", "btn", key);
        button.addEventListener("click", () => A.toast("DTMF " + key));
        keypad.appendChild(button);
      });
      main.appendChild(keypad);

      if (state.log.length) {
        main.appendChild(el("h4", "", "Recent calls"));
        const log = el("div", "log");
        state.log.slice(0, 6).forEach((entry) => {
          log.appendChild(el("div", "", entry.when + " · " + entry.kind + " · " + entry.who + " · " + entry.duration));
        });
        main.appendChild(log);
      }
    } else if (state.tab === "messages") {
      main.appendChild(card);
      const thread = el("div", "log");
      [
        ["Aurora Ops", "Live image is up with the new shell — profiles switch instantly."],
        ["You", "Jasper target at boot, Gates on demand. VoiceConnect is wired into the dock."],
        ["Aurora Ops", "Mic meter falls back honestly when there is no capture device."],
        ["You", "Ship it."]
      ].forEach(([who, text]) => thread.appendChild(el("div", "", who + ": " + text)));
      main.appendChild(thread);
      const compose = el("div");
      compose.style.display = "flex";
      compose.style.gap = "8px";
      const input = document.createElement("input");
      input.type = "text";
      input.placeholder = "Message " + state.active.name + "…";
      input.style.cssText = "flex:1;padding:8px 12px;border-radius:999px;border:1px solid rgba(255,255,255,.2);background:rgba(255,255,255,.08);color:inherit;font:inherit;font-size:12.5px";
      input.addEventListener("keydown", (event) => event.stopPropagation());
      const send = el("button", "btn primary", "Send");
      send.addEventListener("click", () => {
        if (!input.value.trim()) return;
        thread.appendChild(el("div", "", "You: " + input.value.trim()));
        input.value = "";
      });
      compose.append(input, send);
      main.appendChild(compose);
    } else {
      main.appendChild(card);
      main.appendChild(el("h4", "", "Capability probe"));
      selfTest().forEach(([key, value]) => main.appendChild(row(key, value)));
      const buttons = el("div");
      buttons.style.display = "flex";
      buttons.style.gap = "8px";
      const probe = el("button", "btn", "Probe microphone");
      probe.addEventListener("click", () => {
        startMeter(el("i"), el("span", "sub", "probing"));
        navigator.mediaDevices && navigator.mediaDevices.getUserMedia({ audio: true })
          .then(() => A.toast("Microphone permission granted"))
          .catch(() => A.toast("No microphone available — simulated meter in use"));
      });
      const clear = el("button", "btn", "Clear call log");
      clear.addEventListener("click", () => { state.log = []; render(body, ctx); });
      buttons.append(probe, clear);
      main.appendChild(buttons);
    }

    wrap.append(aside, main);
    body.replaceChildren(wrap);
    body.appendChild(el("div", "status", "VoiceConnect 2.0 · local demo transport · no external signalling configured"));
  }

  A.registerApp({
    id: "voiceconnect",
    name: "VoiceConnect",
    glyph: "🎙",
    render(body, ctx) {
      render(body, ctx);
      const observer = () => stopMeter();
      body.closest(".window").addEventListener("aurora:closed", observer, { once: true });
    }
  });

  // Desktop icon for VoiceConnect is part of the default icon set; add a network panel entry.
  A.registerPanel({ id: "voiceconnect", name: "VoiceConnect", glyph: "🎙", category: "communication" });
})();

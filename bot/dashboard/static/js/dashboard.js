/**
 * DiscBot live dashboard — polls API and sends control actions.
 * Design: Nightmare Bots glass / violet system.
 */
(function () {
  const guildInput = document.getElementById("guild-id");
  const tokenInput = document.getElementById("api-token");
  const feedback = document.getElementById("ctrl-feedback");

  // Restore local settings
  const savedGuild = localStorage.getItem("discbot_guild");
  const savedToken = localStorage.getItem("discbot_token");
  if (savedGuild) guildInput.value = savedGuild;
  else if (window.DASHBOARD_DEFAULT_GUILD) guildInput.value = window.DASHBOARD_DEFAULT_GUILD;
  if (savedToken) tokenInput.value = savedToken;

  document.getElementById("save-settings").addEventListener("click", () => {
    localStorage.setItem("discbot_guild", guildInput.value.trim());
    localStorage.setItem("discbot_token", tokenInput.value);
    setFeedback("Saved to this browser.", "ok");
  });

  function guildId() {
    return (guildInput.value || window.DASHBOARD_DEFAULT_GUILD || "").trim();
  }

  function authHeaders() {
    const t = tokenInput.value.trim();
    if (!t) return {};
    return { Authorization: t.startsWith("Bearer ") ? t : `Bearer ${t}` };
  }

  function fmtMs(ms) {
    if (!ms || ms < 0) return "0:00";
    const s = Math.floor(ms / 1000);
    const h = Math.floor(s / 3600);
    const m = Math.floor((s % 3600) / 60);
    const sec = s % 60;
    if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(sec).padStart(2, "0")}`;
    return `${m}:${String(sec).padStart(2, "0")}`;
  }

  function setFeedback(msg, kind) {
    feedback.textContent = msg || "";
    feedback.className =
      "text-xs mt-3 min-h-[1rem] " +
      (kind === "err" ? "text-red-400" : kind === "ok" ? "text-emerald-400" : "text-zinc-500");
  }

  async function getJson(url) {
    const res = await fetch(url, { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error(`${res.status} ${url}`);
    return res.json();
  }

  async function refreshStatus() {
    try {
      const [status, ll] = await Promise.all([
        getJson("/api/status"),
        getJson("/api/lavalink"),
      ]);

      const online = !!status.bot_name && status.bot_name !== "Not ready";
      document.getElementById("stat-bot").textContent = online ? "Online" : "Offline";
      document.getElementById("stat-bot-sub").textContent = status.bot_name || "—";
      document.getElementById("side-bot-status").innerHTML = online
        ? '<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Online'
        : '<span class="w-1.5 h-1.5 rounded-full bg-red-500"></span> Offline';

      document.getElementById("latency-pill").textContent =
        status.latency_ms != null ? `${status.latency_ms} ms` : "— ms";
      if (status.uptime) {
        document.getElementById("uptime-pill").textContent = `uptime ${status.uptime}`;
      }

      document.getElementById("stat-guilds").textContent = status.guild_count ?? "—";
      document.getElementById("stat-vc").textContent =
        `${status.connected_voice_channels ?? 0} voice`;

      const llOk = !!ll.connected;
      document.getElementById("stat-ll").textContent = llOk ? "Connected" : "Down";
      document.getElementById("stat-ll-sub").textContent = llOk
        ? `${ll.latency_ms ?? "?"} ms · ${ll.playing_players ?? 0} playing`
        : "not connected";
      document.getElementById("side-ll-status").textContent = llOk
        ? `${ll.latency_ms ?? "?"}ms`
        : "offline";
      document.getElementById("side-ll-status").className = llOk
        ? "text-emerald-400"
        : "text-red-400";
    } catch (e) {
      console.warn("status poll failed", e);
    }
  }

  async function refreshPlayer() {
    const gid = guildId();
    if (!gid) return;
    try {
      const [np, queue] = await Promise.all([
        getJson(`/api/nowplaying/${gid}`),
        getJson(`/api/queue/${gid}`),
      ]);

      const art = document.getElementById("art");
      const stateEl = document.getElementById("play-state");

      if (np.playing) {
        document.getElementById("np-title").textContent = np.title || "Unknown";
        document.getElementById("np-artist").textContent = np.author || "—";
        document.getElementById("np-pos").textContent = fmtMs(np.position);
        document.getElementById("np-len").textContent = fmtMs(np.length);
        const pct =
          np.length > 0 ? Math.min(100, (100 * (np.position || 0)) / np.length) : 0;
        document.getElementById("np-progress").style.width = `${pct}%`;

        if (np.volume != null) {
          document.getElementById("vol-slider").value = np.volume;
          document.getElementById("vol-label").textContent = `${np.volume}%`;
        }

        stateEl.textContent = np.paused ? "Paused" : "Playing";
        stateEl.className =
          "text-xs px-2 py-0.5 rounded-full border " +
          (np.paused
            ? "border-amber-500/30 bg-amber-500/10 text-amber-300"
            : "border-violet-500/30 bg-violet-500/10 text-violet-300");

        if (np.artwork_url) {
          art.innerHTML = `<img class="art-img" src="${np.artwork_url}" alt="">`;
        }
      } else {
        document.getElementById("np-title").textContent = "Nothing playing";
        document.getElementById("np-artist").textContent = "Use !play in Discord";
        document.getElementById("np-pos").textContent = "0:00";
        document.getElementById("np-len").textContent = "0:00";
        document.getElementById("np-progress").style.width = "0%";
        stateEl.textContent = "Idle";
        stateEl.className =
          "text-xs px-2 py-0.5 rounded-full border border-white/10 text-zinc-500";
        art.innerHTML =
          '<iconify-icon icon="solar:music-note-2-linear" class="text-violet-500/40" width="40"></iconify-icon>';
      }

      const tracks = queue.tracks || [];
      document.getElementById("stat-queue").textContent = String(tracks.length);
      document.getElementById("queue-count").textContent = `${tracks.length} tracks`;
      const list = document.getElementById("queue-list");
      if (!tracks.length) {
        list.innerHTML =
          '<div class="p-6 text-center text-sm text-zinc-600">Queue is empty</div>';
      } else {
        list.innerHTML = tracks
          .slice(0, 50)
          .map(
            (t, i) => `
          <div class="queue-row">
            <span class="text-xs font-mono text-zinc-600 w-5">${i + 1}</span>
            <div class="min-w-0 flex-1">
              <div class="text-sm text-white truncate">${escapeHtml(t.title || "Unknown")}</div>
              <div class="text-xs text-zinc-500 truncate">${escapeHtml(t.author || "")}</div>
            </div>
            <span class="text-xs font-mono text-zinc-600">${fmtMs(t.length)}</span>
          </div>`
          )
          .join("");
      }
    } catch (e) {
      console.warn("player poll failed", e);
    }
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  async function control(action, extra) {
    const gid = guildId();
    if (!gid) {
      setFeedback("Set a guild ID first.", "err");
      return;
    }
    setFeedback(`Sending ${action}…`);
    try {
      const res = await fetch(`/api/control/${gid}/${action}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
          ...authHeaders(),
        },
        body: JSON.stringify(extra || {}),
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) {
        setFeedback(data.detail || `Failed (${res.status})`, "err");
        return;
      }
      setFeedback(data.message || `${action} ok`, "ok");
      refreshPlayer();
    } catch (e) {
      setFeedback(String(e), "err");
    }
  }

  document.querySelectorAll(".ctrl-btn[data-action]").forEach((btn) => {
    btn.addEventListener("click", () => control(btn.dataset.action));
  });

  let volTimer;
  document.getElementById("vol-slider").addEventListener("input", (e) => {
    const v = Number(e.target.value);
    document.getElementById("vol-label").textContent = `${v}%`;
    clearTimeout(volTimer);
    volTimer = setTimeout(() => control("volume", { volume: v }), 300);
  });

  // Nav active state
  document.querySelectorAll(".nav-link").forEach((link) => {
    link.addEventListener("click", () => {
      document.querySelectorAll(".nav-link").forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
    });
  });

  async function tick() {
    await Promise.all([refreshStatus(), refreshPlayer()]);
  }
  tick();
  setInterval(tick, 2500);
})();

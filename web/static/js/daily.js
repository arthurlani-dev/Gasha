/* ==========================================================================
   GASHA — /daily page logic
   --------------------------------------------------------------------------
   Conectado ao backend real em site/app.py (FastAPI). Endpoints usados:
     GET  /api/auth/me            -> { id, username, avatarUrl } | 401
     GET  /auth/discord/login     -> redireciona para o OAuth2 do Discord
     POST /api/auth/logout        -> encerra a sessão
     GET  /api/daily/status       -> { balance, nextClaimAt, streak, claimedDays }
     POST /api/daily/claim        -> { amount, balance, nextClaimAt, streak, claimedDays }
                                      (409 = cooldown ainda ativo)
   ========================================================================== */
(() => {
  "use strict";

  /* ------------------------------------------------------------------ *
   * GashaAPI — única camada que fala com o backend. Se um dia a API
   * mudar de rota, só isso aqui precisa mudar.
   * ------------------------------------------------------------------ */
  const GashaAPI = {
    async getSession() {
      const res = await fetch("/api/auth/me", { credentials: "include" });
      if (!res.ok) return null;
      return res.json();
    },

    async loginWithDiscord() {
      window.location.href = "/auth/discord/login";
      // a navegação já sai da página aqui; nada mais a fazer
    },

    async logout() {
      await fetch("/api/auth/logout", { method: "POST", credentials: "include" });
      return true;
    },

    async getDailyStatus() {
      const res = await fetch("/api/daily/status", { credentials: "include" });
      if (!res.ok) throw new Error("status-failed");
      return res.json();
    },

    async claimDaily() {
      const res = await fetch("/api/daily/claim", { method: "POST", credentials: "include" });
      const data = await res.json();

      if (res.status === 409) {
        const err = new Error("cooldown-active");
        err.secondsLeft = data.segundosRestantes;
        throw err;
      }
      if (!res.ok) throw new Error(data.erro || "claim-failed");

      return data;
    },
  };

  /* ------------------------------------------------------------------ *
   * DOM wiring
   * ------------------------------------------------------------------ */
  const els = {};
  let countdownTimer = null;

  function cacheEls() {
    els.loginBlock = document.querySelector(".daily-login");
    els.app = document.querySelector(".daily-app");
    els.loginBtn = document.querySelector("[data-action='login']");
    els.logoutBtn = document.querySelector("[data-action='logout']");
    els.claimBtn = document.querySelector("[data-action='claim']");
    els.balanceNum = document.querySelector("[data-balance]");
    els.gainPop = document.querySelector("[data-gain-pop]");
    els.cooldownWrap = document.querySelector("[data-cooldown-wrap]");
    els.cooldownTimer = document.querySelector("[data-cooldown-timer]");
    els.streakRow = document.querySelector("[data-streak-row]");
    els.username = document.querySelector("[data-username]");
    els.avatar = document.querySelector("[data-avatar]");
  }

  function formatNumber(n) {
    return n.toLocaleString("pt-BR");
  }

  function renderStreak(claimedDays, streak) {
    if (!els.streakRow) return;
    const days = ["S", "T", "Q", "Q", "S", "S", "D"];
    els.streakRow.innerHTML = days
      .map((label, i) => {
        const done = claimedDays[i];
        const isToday = i === streak - 1;
        const cls = ["streak-day", done ? "is-done" : "", isToday ? "is-today" : ""].filter(Boolean).join(" ");
        const icon = done ? "◆" : "·";
        return `<div class="${cls}"><span>${icon}</span>${label}</div>`;
      })
      .join("");
  }

  function startCountdown(nextClaimAt) {
    clearInterval(countdownTimer);
    if (!nextClaimAt || Date.now() >= nextClaimAt) {
      setClaimReady();
      return;
    }
    setClaimCooldown();
    const tick = () => {
      const remaining = nextClaimAt - Date.now();
      if (remaining <= 0) {
        clearInterval(countdownTimer);
        setClaimReady();
        return;
      }
      const h = Math.floor(remaining / 3600000);
      const m = Math.floor((remaining % 3600000) / 60000);
      const s = Math.floor((remaining % 60000) / 1000);
      if (els.cooldownTimer) {
        els.cooldownTimer.innerHTML =
          `${String(h).padStart(2, "0")}<span class="u">h</span> ` +
          `${String(m).padStart(2, "0")}<span class="u">m</span> ` +
          `${String(s).padStart(2, "0")}<span class="u">s</span>`;
      }
    };
    tick();
    countdownTimer = setInterval(tick, 1000);
  }

  function setClaimReady() {
    if (els.claimBtn) {
      els.claimBtn.disabled = false;
      els.claimBtn.classList.remove("is-cooldown");
      els.claimBtn.querySelector(".claim-btn-label").textContent = "Coletar";
      els.claimBtn.querySelector(".claim-btn-sub").textContent = "Toque para abrir";
    }
    if (els.cooldownWrap) els.cooldownWrap.style.display = "none";
  }

  function setClaimCooldown() {
    if (els.claimBtn) {
      els.claimBtn.disabled = true;
      els.claimBtn.classList.add("is-cooldown");
      els.claimBtn.querySelector(".claim-btn-label").textContent = "Coletado";
      els.claimBtn.querySelector(".claim-btn-sub").textContent = "Volte amanhã";
    }
    if (els.cooldownWrap) els.cooldownWrap.style.display = "";
  }

  async function refreshFromStatus() {
    const status = await GashaAPI.getDailyStatus();
    if (els.balanceNum) els.balanceNum.textContent = formatNumber(status.balance);
    renderStreak(status.claimedDays, status.streak);
    startCountdown(status.nextClaimAt);
  }

  async function handleClaim() {
    if (!els.claimBtn || els.claimBtn.disabled) return;
    els.claimBtn.disabled = true;
    try {
      const result = await GashaAPI.claimDaily();

      // balance count-up
      animateBalance(result.balance - result.amount, result.balance);

      // floating "+N" pop
      if (els.gainPop) {
        els.gainPop.textContent = `+${formatNumber(result.amount)} Pixels`;
        els.gainPop.classList.remove("is-animating");
        void els.gainPop.offsetWidth; // restart animation
        els.gainPop.classList.add("is-animating");
      }

      // confetti burst from button center, reuses main.js's spawnBurst via a synthetic click target
      const rect = els.claimBtn.getBoundingClientRect();
      window.dispatchEvent(
        new CustomEvent("gasha:burst", { detail: { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } })
      );

      renderStreak(result.claimedDays, result.streak);
      startCountdown(result.nextClaimAt);
    } catch (err) {
      // Se o servidor disse que o cooldown já estava ativo (ex: outra aba
      // coletou primeiro), resincroniza com o estado real em vez de só
      // liberar o botão de novo.
      console.warn("Falha ao coletar recompensa:", err.message);
      try {
        await refreshFromStatus();
      } catch {
        setClaimReady();
      }
    }
  }

  function animateBalance(from, to) {
    if (!els.balanceNum) return;
    const duration = 900;
    const start = performance.now();
    const tick = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      els.balanceNum.textContent = formatNumber(Math.round(from + (to - from) * eased));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  async function showLoggedIn(session) {
    if (els.loginBlock) els.loginBlock.classList.add("is-hidden");
    if (els.app) els.app.classList.add("is-active");
    if (els.username) els.username.textContent = session.username;
    if (els.avatar && session.avatarUrl) els.avatar.src = session.avatarUrl;
    await refreshFromStatus();
  }

  function showLoggedOut() {
    if (els.loginBlock) els.loginBlock.classList.remove("is-hidden");
    if (els.app) els.app.classList.remove("is-active");
    clearInterval(countdownTimer);
  }

  async function init() {
    cacheEls();

    if (els.loginBtn) {
      els.loginBtn.addEventListener("click", async () => {
        els.loginBtn.disabled = true;
        els.loginBtn.textContent = "Conectando…";
        await GashaAPI.loginWithDiscord();
      });
    }

    if (els.logoutBtn) {
      els.logoutBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        await GashaAPI.logout();
        showLoggedOut();
      });
    }

    if (els.claimBtn) {
      els.claimBtn.addEventListener("click", handleClaim);
    }

    // reuse the confetti burst helper defined in main.js if present
    window.addEventListener("gasha:burst", (e) => {
      if (typeof window.gashaSpawnBurst === "function") {
        window.gashaSpawnBurst(e.detail.x, e.detail.y);
      }
    });

    try {
      const session = await GashaAPI.getSession();
      if (session) {
        await showLoggedIn(session);
      } else {
        showLoggedOut();
      }
    } catch {
      showLoggedOut();
    }
  }

  document.addEventListener("DOMContentLoaded", init);
})();

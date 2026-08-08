/* ==========================================================================
   GASHA — shared front-end behaviour
   No framework, no build step: small focused modules, defensive querying
   (every module bails out quietly if its markup isn't on the page).
   ========================================================================== */
(() => {
  "use strict";

  const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------------ *
   * Navbar: shrink + blur on scroll, mobile menu toggle
   * ------------------------------------------------------------------ */
  const initNav = () => {
    const nav = document.querySelector(".nav");
    if (!nav) return;

    const onScroll = () => {
      nav.classList.toggle("is-scrolled", window.scrollY > 12);
    };
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });

    const burger = document.querySelector(".nav-burger");
    const panel = document.querySelector(".mobile-panel");
    if (burger && panel) {
      const closeMenu = () => {
        burger.classList.remove("is-open");
        panel.classList.remove("is-open");
        document.body.style.overflow = "";
      };
      burger.addEventListener("click", () => {
        const willOpen = !panel.classList.contains("is-open");
        burger.classList.toggle("is-open", willOpen);
        burger.setAttribute("aria-expanded", String(willOpen));
        panel.classList.toggle("is-open", willOpen);
        document.body.style.overflow = willOpen ? "hidden" : "";
      });
      panel.querySelectorAll("a").forEach((a) => a.addEventListener("click", closeMenu));
    }

    // highlight current section in nav while scrolling (home page only)
    const sections = document.querySelectorAll("main [id]");
    const links = document.querySelectorAll(".nav-links a[href^='#'], .mobile-panel a[href^='#']");
    if (sections.length && links.length && "IntersectionObserver" in window) {
      const map = new Map();
      links.forEach((l) => map.set(l.getAttribute("href").slice(1), l));
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            const link = map.get(entry.target.id);
            if (!link) return;
            if (entry.isIntersecting) {
              links.forEach((l) => l.classList.remove("is-active"));
              link.classList.add("is-active");
            }
          });
        },
        { rootMargin: "-45% 0px -50% 0px" }
      );
      sections.forEach((s) => io.observe(s));
    }
  };

  /* ------------------------------------------------------------------ *
   * Scroll reveal
   * ------------------------------------------------------------------ */
  const initReveal = () => {
    const items = document.querySelectorAll(".reveal");
    if (!items.length) return;

    if (prefersReducedMotion || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }

    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return;
          const group = entry.target.closest(".reveal-stagger");
          if (group) {
            [...group.children].forEach((child, i) => child.style.setProperty("--i", i));
          }
          entry.target.classList.add("is-visible");
          obs.unobserve(entry.target);
        });
      },
      { threshold: 0.15, rootMargin: "0px 0px -60px 0px" }
    );
    items.forEach((el) => io.observe(el));
  };

  /* ------------------------------------------------------------------ *
   * Real stats — fetches /api/stats (web/app.py) and replaces the
   * illustrative HTML values with live numbers from the bot's database.
   * Polls periodically so the numbers stay current while the page is
   * open. If the API doesn't respond (e.g. backend offline, or the site
   * opened straight from a file), the illustrative placeholders from the
   * HTML stay in place instead of breaking the section.
   * ------------------------------------------------------------------ */
  const STATS_POLL_MS = 30000;

  const applyStatValues = (data, { animate: shouldAnimate }) => {
    const nums = document.querySelectorAll("[data-stat]");
    if (!nums.length) return;

    const valores = {
      servidores: data.servidores,
      usuarios: data.usuarios,
      comandos: data.comandos_executados,
      pixels: data.pixels_distribuidos,
    };

    nums.forEach((el) => {
      const valor = valores[el.dataset.stat];
      if (typeof valor !== "number") return;

      // Real numbers come in as whole integers, no fake decimals/suffix
      el.dataset.count = valor;
      el.removeAttribute("data-decimals");
      el.dataset.suffix = "+";

      if (shouldAnimate) return; // entrance animation (initCounters) handles this pass

      // Background refresh: only re-render if the value actually moved,
      // with a short tween instead of the long entrance animation.
      const previous = parseFloat(el.dataset.current || el.dataset.count);
      if (previous === valor) return;
      tweenStatNumber(el, previous, valor, 700);
    });
  };

  const tweenStatNumber = (el, from, to, duration) => {
    const suffix = el.dataset.suffix || "";
    const start = performance.now();
    const step = (now) => {
      const p = Math.min(1, (now - start) / duration);
      const eased = 1 - Math.pow(1 - p, 3);
      const value = from + (to - from) * eased;
      el.textContent = Math.round(value).toLocaleString("en-US") + suffix;
      el.dataset.current = value;
      if (p < 1) requestAnimationFrame(step);
      else el.dataset.current = to;
    };
    requestAnimationFrame(step);
  };

  const fetchRealStats = async ({ animate = false } = {}) => {
    const nums = document.querySelectorAll("[data-stat]");
    if (!nums.length) return;

    try {
      const res = await fetch("/api/stats", { credentials: "include" });
      if (!res.ok) throw new Error("stats unavailable");
      const data = await res.json();
      applyStatValues(data, { animate });
    } catch (err) {
      // Backend offline (or site opened directly from a file) — the
      // illustrative numbers defined in the HTML remain in place.
      console.info("Real stats unavailable, using illustrative values.");
    }
  };

  const startStatsPolling = () => {
    const nums = document.querySelectorAll("[data-stat]");
    if (!nums.length) return;
    setInterval(() => fetchRealStats({ animate: false }), STATS_POLL_MS);
  };

  /* ------------------------------------------------------------------ *
   * Animated counters (stats section) — counts up once when in view.
   * Reads target from data-count, optional data-decimals / data-suffix.
   * ------------------------------------------------------------------ */
  const initCounters = () => {
    const nums = document.querySelectorAll("[data-count]");
    if (!nums.length) return;

    const animate = (el) => {
      const target = parseFloat(el.dataset.count);
      const decimals = parseInt(el.dataset.decimals || "0", 10);
      const suffix = el.dataset.suffix || "";
      const duration = 1600;
      const start = performance.now();

      if (prefersReducedMotion) {
        el.textContent = (decimals > 0 ? target.toFixed(decimals) : Math.round(target).toLocaleString("en-US")) + suffix;
        el.dataset.current = target;
        return;
      }

      const tick = (now) => {
        const p = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - p, 3);
        const value = target * eased;
        el.textContent = (decimals > 0 ? value.toFixed(decimals) : Math.round(value).toLocaleString("en-US")) + suffix;
        el.dataset.current = value;
        if (p < 1) requestAnimationFrame(tick);
        else el.dataset.current = target;
      };
      requestAnimationFrame(tick);
    };

    if (!("IntersectionObserver" in window)) {
      nums.forEach(animate);
      return;
    }
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animate(entry.target);
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.6 }
    );
    nums.forEach((el) => io.observe(el));
  };

  /* ------------------------------------------------------------------ *
   * XP demo bar — fills once visible
   * ------------------------------------------------------------------ */
  const initXpBar = () => {
    const track = document.querySelector(".xp-track");
    if (!track || !("IntersectionObserver" in window)) return;
    const io = new IntersectionObserver(
      (entries, obs) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("in-view");
            obs.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.5 }
    );
    io.observe(track);
  };

  /* ------------------------------------------------------------------ *
   * FAQ accordion
   * ------------------------------------------------------------------ */
  const initFaq = () => {
    const items = document.querySelectorAll(".faq-item");
    if (!items.length) return;
    items.forEach((item) => {
      const q = item.querySelector(".faq-q");
      const a = item.querySelector(".faq-a");
      q.addEventListener("click", () => {
        const isOpen = item.classList.contains("is-open");
        items.forEach((other) => {
          other.classList.remove("is-open");
          other.querySelector(".faq-a").style.maxHeight = null;
          other.querySelector(".faq-q").setAttribute("aria-expanded", "false");
        });
        if (!isOpen) {
          item.classList.add("is-open");
          a.style.maxHeight = a.scrollHeight + "px";
          q.setAttribute("aria-expanded", "true");
        }
      });
    });
  };

  /* ------------------------------------------------------------------ *
   * Dopamine burst — small confetti of capsule-colored dots from any
   * element carrying [data-burst] on click (used on primary CTAs).
   * ------------------------------------------------------------------ */
  const spawnBurst = (x, y) => {
    if (prefersReducedMotion) return;
    const colors = ["#f5b942", "#ff4fa3", "#7c4dff", "#ffd684"];
    const count = 14;
    for (let i = 0; i < count; i++) {
      const p = document.createElement("span");
      p.className = "burst-particle";
      const angle = (Math.PI * 2 * i) / count + Math.random() * 0.4;
      const dist = 60 + Math.random() * 70;
      const size = 5 + Math.random() * 6;
      p.style.setProperty("--dx", `${Math.cos(angle) * dist}px`);
      p.style.setProperty("--dy", `${Math.sin(angle) * dist - 20}px`);
      p.style.left = `${x - size / 2}px`;
      p.style.top = `${y - size / 2}px`;
      p.style.width = `${size}px`;
      p.style.height = `${size}px`;
      p.style.background = colors[i % colors.length];
      document.body.appendChild(p);
      p.addEventListener("animationend", () => p.remove());
    }
  };

  window.gashaSpawnBurst = spawnBurst;

  const initBursts = () => {
    document.querySelectorAll("[data-burst]").forEach((el) => {
      el.addEventListener("click", (e) => {
        spawnBurst(e.clientX || e.target.getBoundingClientRect().left, e.clientY || e.target.getBoundingClientRect().top);
      });
    });
  };

  /* ------------------------------------------------------------------ *
   * Footer year
   * ------------------------------------------------------------------ */
  const initYear = () => {
    const el = document.querySelector("[data-year]");
    if (el) el.textContent = new Date().getFullYear();
  };

  document.addEventListener("DOMContentLoaded", async () => {
    initNav();
    initReveal();
    await fetchRealStats({ animate: true }); // swaps data-count for real values before animating
    initCounters();
    initXpBar();
    initFaq();
    initBursts();
    initYear();
    startStatsPolling(); // keeps the numbers live while the page stays open
  });
})();

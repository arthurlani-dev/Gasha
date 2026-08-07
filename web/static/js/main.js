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
   * Estatísticas reais — busca /api/stats (site/app.py) e substitui os
   * valores ilustrativos do HTML antes de animar. Se a API não responder
   * (ex: site aberto sem o backend rodando), mantém os placeholders do
   * próprio HTML como fallback, sem quebrar a seção.
   * ------------------------------------------------------------------ */
  const fetchRealStats = async () => {
    const nums = document.querySelectorAll("[data-stat]");
    if (!nums.length) return;

    try {
      const res = await fetch("/api/stats", { credentials: "include" });
      if (!res.ok) throw new Error("stats indisponíveis");
      const data = await res.json();

      const valores = {
        servidores: data.servidores,
        usuarios: data.usuarios,
        comandos: data.comandos_executados,
        pixels: data.pixels_distribuidos,
      };

      nums.forEach((el) => {
        const valor = valores[el.dataset.stat];
        if (typeof valor !== "number") return;
        // Números reais entram inteiros, sem casas decimais fictícias
        el.dataset.count = valor;
        el.removeAttribute("data-decimals");
        el.dataset.suffix = "+";
      });
    } catch (err) {
      // Backend fora do ar (ou site aberto direto do arquivo) — os
      // números ilustrativos definidos no HTML seguem valendo.
      console.info("Estatísticas reais indisponíveis, usando valores ilustrativos.");
    }
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
        el.textContent = (decimals > 0 ? target.toFixed(decimals) : Math.round(target).toLocaleString("pt-BR")) + suffix;
        return;
      }

      const tick = (now) => {
        const p = Math.min(1, (now - start) / duration);
        const eased = 1 - Math.pow(1 - p, 3);
        const value = target * eased;
        el.textContent = (decimals > 0 ? value.toFixed(decimals) : Math.round(value).toLocaleString("pt-BR")) + suffix;
        if (p < 1) requestAnimationFrame(tick);
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
    await fetchRealStats(); // troca os data-count pelos valores reais antes de animar
    initCounters();
    initXpBar();
    initFaq();
    initBursts();
    initYear();
  });
})();

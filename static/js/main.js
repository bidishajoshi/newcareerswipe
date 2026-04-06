/* ── CareerSwipe · main.js ───────────────────────────────────────────────── */

// Auto-dismiss flash messages after 4s
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".flash").forEach(el => {
    setTimeout(() => {
      el.style.transition = "opacity 0.5s";
      el.style.opacity = "0";
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });
});

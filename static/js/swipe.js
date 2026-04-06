/* ── CareerSwipe · swipe.js ──────────────────────────────────────────────── */
(function () {
  const stack     = document.getElementById("swipeStack");
  const btnSkip   = document.getElementById("btnSkip");
  const btnApply  = document.getElementById("btnApply");
  const overlaySkip  = document.getElementById("overlaySkip");
  const overlayApply = document.getElementById("overlayApply");

  if (!stack) return;

  let isDragging = false;
  let startX = 0, startY = 0, currentX = 0;
  let activeCard = null;

  function getTopCard() {
    const cards = stack.querySelectorAll(".job-card:not(.fly-right):not(.fly-left)");
    return cards[cards.length - 1] || null;
  }

  // ── Drag (mouse) ──────────────────────────────────────────────────────────
  stack.addEventListener("mousedown", e => {
    const card = e.target.closest(".job-card");
    if (!card || card !== getTopCard()) return;
    isDragging = true;
    activeCard = card;
    startX = e.clientX;
    startY = e.clientY;
    card.style.transition = "none";
    e.preventDefault();
  });

  document.addEventListener("mousemove", e => {
    if (!isDragging || !activeCard) return;
    currentX = e.clientX - startX;
    const rotate = currentX * 0.08;
    activeCard.style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;

    if (currentX > 60) {
      activeCard.classList.add("swiping-right");
      activeCard.classList.remove("swiping-left");
    } else if (currentX < -60) {
      activeCard.classList.add("swiping-left");
      activeCard.classList.remove("swiping-right");
    } else {
      activeCard.classList.remove("swiping-right", "swiping-left");
    }
  });

  document.addEventListener("mouseup", () => {
    if (!isDragging || !activeCard) return;
    isDragging = false;
    activeCard.style.transition = "";

    if (currentX > 80) {
      doSwipe(activeCard, "right");
    } else if (currentX < -80) {
      doSwipe(activeCard, "left");
    } else {
      // Snap back
      activeCard.style.transform = "";
      activeCard.classList.remove("swiping-right", "swiping-left");
    }
    activeCard = null;
    currentX = 0;
  });

  // ── Touch ─────────────────────────────────────────────────────────────────
  stack.addEventListener("touchstart", e => {
    const card = e.target.closest(".job-card");
    if (!card || card !== getTopCard()) return;
    isDragging = true;
    activeCard = card;
    startX = e.touches[0].clientX;
    startY = e.touches[0].clientY;
    card.style.transition = "none";
  }, { passive: true });

  stack.addEventListener("touchmove", e => {
    if (!isDragging || !activeCard) return;
    currentX = e.touches[0].clientX - startX;
    const rotate = currentX * 0.08;
    activeCard.style.transform = `translateX(${currentX}px) rotate(${rotate}deg)`;
    if (currentX > 60) {
      activeCard.classList.add("swiping-right");
      activeCard.classList.remove("swiping-left");
    } else if (currentX < -60) {
      activeCard.classList.add("swiping-left");
      activeCard.classList.remove("swiping-right");
    } else {
      activeCard.classList.remove("swiping-right", "swiping-left");
    }
  }, { passive: true });

  stack.addEventListener("touchend", () => {
    if (!isDragging || !activeCard) return;
    isDragging = false;
    activeCard.style.transition = "";
    if (currentX > 80) {
      doSwipe(activeCard, "right");
    } else if (currentX < -80) {
      doSwipe(activeCard, "left");
    } else {
      activeCard.style.transform = "";
      activeCard.classList.remove("swiping-right", "swiping-left");
    }
    activeCard = null;
    currentX = 0;
  });

  // ── Keyboard ──────────────────────────────────────────────────────────────
  document.addEventListener("keydown", e => {
    const card = getTopCard();
    if (!card) return;
    if (e.key === "ArrowRight") doSwipe(card, "right");
    if (e.key === "ArrowLeft")  doSwipe(card, "left");
  });

  // ── Buttons ───────────────────────────────────────────────────────────────
  btnSkip?.addEventListener("click", () => {
    const card = getTopCard();
    if (card) doSwipe(card, "left");
  });

  btnApply?.addEventListener("click", () => {
    const card = getTopCard();
    if (card) doSwipe(card, "right");
  });

  // ── Core swipe logic ──────────────────────────────────────────────────────
  function doSwipe(card, direction) {
    const jobId = card.dataset.jobId;

    // Animate fly-away
    card.classList.add(direction === "right" ? "fly-right" : "fly-left");
    card.classList.remove("swiping-right", "swiping-left");

    // Show overlay
    const overlay = direction === "right" ? overlayApply : overlaySkip;
    overlay.classList.add("show");
    setTimeout(() => overlay.classList.remove("show"), 900);

    // POST to server
    fetch("/swipe", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ job_id: jobId, direction })
    })
    .then(r => r.json())
    .then(data => {
      if (data.direction === "right") {
        showToast("✅ Application sent!");
      }
    })
    .catch(() => {});

    // Remove card from DOM after animation
    setTimeout(() => {
      card.remove();
      updateStackPeek();
      if (!getTopCard()) showAllDoneMessage();
    }, 420);
  }

  function updateStackPeek() {
    // Re-applying nth-last-child styles is handled by CSS automatically
  }

  function showAllDoneMessage() {
    if (!stack.querySelector(".all-done")) {
      stack.innerHTML = `
        <div class="all-done" style="text-align:center;padding:3rem 1rem;color:#6b6b7a">
          <div style="font-size:3rem;margin-bottom:1rem">🎉</div>
          <h3 style="color:#1a1a2e;margin-bottom:8px">You've seen all jobs!</h3>
          <p style="font-size:14px">Check back later for new listings.</p>
        </div>`;
    }
  }

  // ── Toast helper ──────────────────────────────────────────────────────────
  function showToast(msg) {
    const t = document.createElement("div");
    t.textContent = msg;
    t.style.cssText = `
      position: fixed; bottom: 2rem; left: 50%; transform: translateX(-50%);
      background: #1a1a2e; color: #fff; padding: 10px 20px;
      border-radius: 20px; font-size: 13px; z-index: 9999;
      opacity: 0; transition: opacity 0.3s;
    `;
    document.body.appendChild(t);
    requestAnimationFrame(() => { t.style.opacity = "1"; });
    setTimeout(() => {
      t.style.opacity = "0";
      setTimeout(() => t.remove(), 300);
    }, 2500);
  }
})();

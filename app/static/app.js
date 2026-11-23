// Dua Kelinci sales dashboard: page behaviour + a small same-origin router.
// Every page is a normal server-rendered page; this script only enhances it.
// Without JavaScript, links do full page loads and tables show in server order.
(() => {
  "use strict";

  const PAGE_KEYS = { "/": "ringkasan", "/wilayah-merek": "wilayah-merek", "/outlet-terlemah": "outlet-terlemah" };
  const ROUTES = new Set(Object.keys(PAGE_KEYS));
  const MIN_SKELETON_MS = 350;
  const collator = new Intl.Collator("id", { sensitivity: "base", numeric: true });
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
  const isCoarsePointer = () => window.matchMedia("(pointer: coarse)").matches;
  const matchesQuery = (haystack, rawQuery) => {
    const q = rawQuery.trim().toLowerCase();
    if (!q) return true;
    return q.split(/\s+/).every((token) => haystack.includes(token));
  };

  // ---------------------------------------------------------------- copy
  function initCopy(root) {
    root.querySelectorAll("[data-copy]").forEach((button) => {
      const text = document.getElementById(button.dataset.copy);
      const status = document.getElementById(button.dataset.status);
      if (!text || !status) return;
      let statusTimer;
      let iconTimer;
      const say = (msg, ok) => {
        status.textContent = msg;
        status.classList.toggle("ok", ok);
        clearTimeout(statusTimer);
        statusTimer = setTimeout(() => { status.textContent = ""; status.classList.remove("ok"); }, 5000);
        if (ok) {
          button.dataset.copied = "true";
          clearTimeout(iconTimer);
          iconTimer = setTimeout(() => { delete button.dataset.copied; }, 1800);
        }
      };
      button.addEventListener("click", async () => {
        try {
          if (navigator.clipboard && window.isSecureContext) {
            await navigator.clipboard.writeText(text.value);
          } else {
            text.select();
            if (!document.execCommand("copy")) throw new Error("copy failed");
          }
          say("Tersalin ke clipboard.", true);
        } catch {
          text.focus();
          text.select();
          say("Teks dipilih — tekan Ctrl+C.", false);
        }
      });
    });
  }

  // ---------------------------------------------------------------- sorting
  const cellValue = (cell, kind) => {
    const raw = cell.dataset.value ?? cell.textContent.trim();
    if (kind === "num") return raw === "" ? null : Number(raw);
    return raw;
  };

  function sortTable(table, th, dir) {
    const kind = th.dataset.sort;
    const idx = th.cellIndex;
    const tbody = table.tBodies[0];
    const rows = [...tbody.rows].filter((row) => !row.classList.contains("empty-row"));
    const sign = dir === "ascending" ? 1 : -1;
    rows.sort((a, b) => {
      const va = cellValue(a.cells[idx], kind);
      const vb = cellValue(b.cells[idx], kind);
      if (va === null && vb === null) return 0;
      if (va === null) return 1;
      if (vb === null) return -1;
      return sign * (kind === "num" ? va - vb : collator.compare(va, vb));
    });
    const empty = tbody.querySelector(".empty-row");
    rows.forEach((row) => tbody.insertBefore(row, empty));
    table.querySelectorAll("th[data-sort]").forEach((h) => h.removeAttribute("aria-sort"));
    th.setAttribute("aria-sort", dir);
  }

  function initSortable(root) {
    root.querySelectorAll("table.sortable").forEach((table) => {
      table.querySelectorAll("th[data-sort]").forEach((th) => {
        th.querySelector(".sort-btn").addEventListener("click", () => {
          const dir = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
          sortTable(table, th, dir);
          table.dispatchEvent(new CustomEvent("sorted", { detail: { index: th.cellIndex, dir } }));
        });
      });
    });
  }

  // ---------------------------------------------------------------- outlet table
  function initOutletTable(root) {
    const table = root.querySelector("#outlet-table");
    const toolbar = root.querySelector("[data-outlet-toolbar]");
    const filterStrip = root.querySelector("[data-outlet-filters]");
    if (!table || !toolbar || !filterStrip) return;
    const sortWrap = filterStrip.querySelector("[data-outlet-sort]");
    const statusGroup = root.querySelector("[data-status-group]");
    toolbar.hidden = false;
    filterStrip.hidden = false;
    if (sortWrap) sortWrap.hidden = false;

    const search = toolbar.querySelector("#outlet-search");
    const region = filterStrip.querySelector("#f-region");
    const branch = filterStrip.querySelector("#f-branch");
    const salesman = filterStrip.querySelector("#f-salesman");
    const type = filterStrip.querySelector("#f-type");
    const sortSelect = sortWrap?.querySelector("#outlet-sort");
    const count = root.querySelector("[data-outlet-count]");
    const resetButtons = [...root.querySelectorAll("[data-outlet-reset]")];
    const lineReset = root.querySelector(".result-info [data-outlet-reset]");
    const emptyRow = table.querySelector(".empty-row");
    const emptyQuery = table.querySelector("[data-empty-query]");
    const rows = [...table.tBodies[0].rows].filter((row) => !row.classList.contains("empty-row"));
    const statusValue = () => statusGroup?.querySelector('input[name="status"]:checked')?.value || "";

    function apply() {
      const rawQuery = search.value.trim();
      const st = statusValue();
      let shown = 0;
      rows.forEach((row) => {
        const match =
          matchesQuery(row.dataset.search || "", rawQuery) &&
          (!region.value || row.dataset.region === region.value) &&
          (!branch?.value || row.dataset.branch === branch.value) &&
          (!salesman?.value || (row.dataset.salesmen || "").split("|").includes(salesman.value)) &&
          (!type.value || row.dataset.type === type.value) &&
          (!st || row.dataset.status.split(" ").includes(st));
        row.hidden = !match;
        if (match) shown += 1;
      });
      const filtered = Boolean(rawQuery || region.value || branch?.value || salesman?.value || type.value || st);
      emptyRow.hidden = shown > 0;
      emptyQuery.textContent = rawQuery ? ` dengan “${rawQuery}”` : "";
      count.textContent = filtered ? `Menampilkan ${shown} dari ${rows.length} outlet` : `${rows.length} outlet`;
      if (lineReset) lineReset.hidden = !filtered;
    }

    function reset() {
      search.value = "";
      region.value = "";
      if (branch) branch.value = "";
      if (salesman) salesman.value = "";
      type.value = "";
      const all = statusGroup?.querySelector('input[name="status"][value=""]');
      if (all) {
        all.checked = true;
        all.dispatchEvent(new Event("change", { bubbles: true }));
      }
      apply();
      if (!isCoarsePointer()) search.focus();
    }

    search.addEventListener("input", apply);
    [region, branch, salesman, type].filter(Boolean).forEach((el) => el.addEventListener("change", apply));
    statusGroup?.querySelectorAll('input[name="status"]').forEach((el) => el.addEventListener("change", apply));
    resetButtons.forEach((btn) => btn.addEventListener("click", reset));

    if (sortSelect) {
      const headers = [...table.tHead.rows[0].cells];
      sortSelect.addEventListener("change", () => {
        const [index, dir] = sortSelect.value.split(":");
        if (dir) sortTable(table, headers[Number(index)], dir);
      });
      table.addEventListener("sorted", (event) => {
        const value = `${event.detail.index}:${event.detail.dir}`;
        sortSelect.value = [...sortSelect.options].some((o) => o.value === value) ? value : "custom";
      });
    }
  }

  // ---------------------------------------------------------------- segmented control
  function initSegmented(root) {
    root.querySelectorAll(".segmented").forEach((group) => {
      const indicator = group.querySelector(".seg-indicator");
      if (!indicator) return;
      const place = () => {
        const label = group.querySelector("input:checked")?.closest("label");
        if (!label) return;
        indicator.style.width = `${label.offsetWidth}px`;
        indicator.style.height = `${label.offsetHeight}px`;
        indicator.style.translate = `${label.offsetLeft}px ${label.offsetTop}px`;
      };
      const jump = () => {
        indicator.style.transition = "none";
        place();
        void indicator.offsetWidth;
        indicator.style.transition = "";
      };
      jump();
      group.classList.add("is-ready");
      group.addEventListener("change", place);
      new ResizeObserver(jump).observe(group);
      document.fonts?.ready.then(jump);
    });
  }

  // ---------------------------------------------------------------- dimension underline tabs
  function initViewSwitch(root) {
    const nav = root.querySelector("[data-dim-nav]");
    if (!nav) return;
    const tabs = [...nav.querySelectorAll("[data-dim-tab]")];
    const views = [...root.querySelectorAll("[data-view]")];

    const revealTab = (tab, smooth = false) => {
      if (!tab || nav.scrollWidth <= nav.clientWidth) return;
      const targetLeft = tab.offsetLeft - (nav.clientWidth - tab.offsetWidth) / 2;
      nav.scrollTo({
        left: Math.max(0, Math.min(nav.scrollWidth - nav.clientWidth, targetLeft)),
        behavior: smooth ? "smooth" : "instant",
      });
    };

    const initialTab = tabs.find((t) => t.getAttribute("aria-current") === "page");
    if (initialTab) requestAnimationFrame(() => revealTab(initialTab, false));

    tabs.forEach((tab) => {
      tab.addEventListener("click", (event) => {
        if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
        event.preventDefault();
        const nextKey = tab.dataset.dimTab;
        tabs.forEach((t) => {
          if (t.dataset.dimTab === nextKey) t.setAttribute("aria-current", "page");
          else t.removeAttribute("aria-current");
        });
        revealTab(tab, true);
        views.forEach((view) => {
          const active = view.dataset.view === nextKey;
          view.hidden = !active;
          if (active) {
            view.classList.remove("is-entering");
            void view.offsetWidth;
            view.classList.add("is-entering");
          }
        });
        const url = new URL(location.href);
        url.searchParams.set("lihat", nextKey);
        history.replaceState(history.state, "", url);
      });
    });
  }

  // ---------------------------------------------------------------- quick table search (wilayah/cabang/merek/salesman)
  function initQuickTables(root) {
    root.querySelectorAll("[data-quick-toolbar]").forEach((toolbar) => {
      const section = toolbar.closest(".table-section");
      const table = section?.querySelector("table.data");
      const input = toolbar.querySelector("[data-quick-input]");
      const countEl = section?.querySelector("[data-quick-count]");
      const lineReset = section?.querySelector(".table-title-inline [data-quick-reset]");
      const emptyRow = table?.querySelector(".empty-row");
      const emptyQuery = table?.querySelector("[data-empty-query]");
      if (!table || !input || !countEl) return;

      toolbar.hidden = false;
      const noun = countEl.dataset.noun || "baris";
      const rows = [...table.tBodies[0].rows].filter((r) => !r.classList.contains("empty-row"));
      const defaultLabel = countEl.dataset.defaultLabel || `${rows.length} ${noun}`;
      const resetBtns = [...section.querySelectorAll("[data-quick-reset]")];

      function apply() {
        const rawQuery = input.value.trim();
        let shown = 0;
        rows.forEach((row) => {
          const match = matchesQuery(row.dataset.search || "", rawQuery);
          row.hidden = !match;
          if (match) shown += 1;
        });
        const filtered = Boolean(rawQuery);
        if (emptyRow) emptyRow.hidden = shown > 0;
        if (emptyQuery) emptyQuery.textContent = rawQuery ? ` dengan “${rawQuery}”` : "";
        countEl.textContent = filtered ? `Menampilkan ${shown} dari ${rows.length} ${noun}` : defaultLabel;
        if (lineReset) lineReset.hidden = !filtered;
      }

      input.addEventListener("input", apply);
      resetBtns.forEach((btn) =>
        btn.addEventListener("click", () => {
          input.value = "";
          apply();
          if (!isCoarsePointer()) input.focus();
        })
      );
      apply();
    });
  }

  // ---------------------------------------------------------------- dual-lens switch & search on outlet terlemah
  function initLensSwitch(root) {
    const container = root.querySelector("[data-lens-root]");
    if (!container) return;
    const switcher = container.querySelector("[data-lens-switch]");
    const panels = [...container.querySelectorAll("[data-lens-panel]")];
    const toolbar = container.querySelector("[data-weak-toolbar]");
    const searchInput = toolbar?.querySelector("#weak-search");
    const countEl = container.querySelector("[data-weak-count]");
    const lineReset = container.querySelector(".table-title-inline [data-weak-reset]");
    const resetBtns = [...container.querySelectorAll("[data-weak-reset]")];

    if (switcher && panels.length >= 2) switcher.hidden = false;
    if (toolbar && searchInput) toolbar.hidden = false;

    const applySearch = () => {
      const activePanel = panels.find((p) => !p.hidden) || panels[0];
      const table = activePanel?.querySelector("table.data");
      if (!table || !countEl) return;
      const rawQuery = searchInput ? searchInput.value.trim() : "";
      const rows = [...table.tBodies[0].rows].filter((r) => !r.classList.contains("empty-row"));
      const emptyRow = table.querySelector(".empty-row");
      const emptyQuery = table.querySelector("[data-empty-query]");
      let shown = 0;
      rows.forEach((row) => {
        const match = matchesQuery(row.dataset.search || "", rawQuery);
        row.hidden = !match;
        if (match) shown += 1;
      });
      const filtered = Boolean(rawQuery);
      if (emptyRow) emptyRow.hidden = shown > 0;
      if (emptyQuery) emptyQuery.textContent = rawQuery ? ` dengan “${rawQuery}”` : "";
      countEl.textContent = filtered ? `Menampilkan ${shown} dari ${rows.length} outlet` : `${rows.length} outlet`;
      if (lineReset) lineReset.hidden = !filtered;
    };

    const sync = (animate = false) => {
      if (switcher && panels.length >= 2) {
        const selected = switcher.querySelector("input:checked")?.value || "pct";
        panels.forEach((panel) => {
          const active = panel.dataset.lensPanel === selected;
          panel.hidden = !active;
          if (active && animate) {
            panel.classList.remove("is-entering");
            void panel.offsetWidth;
            panel.classList.add("is-entering");
          }
        });
      }
      applySearch();
    };

    sync(false);
    switcher?.addEventListener("change", () => sync(true));
    searchInput?.addEventListener("input", applySearch);
    resetBtns.forEach((btn) =>
      btn.addEventListener("click", () => {
        if (!searchInput) return;
        searchInput.value = "";
        applySearch();
        if (!isCoarsePointer()) searchInput.focus();
      })
    );
  }

  // ---------------------------------------------------------------- Notion-style outlet side peek
  let peekAbort = null;

  function initSidePeek(root) {
    peekAbort?.abort();
    peekAbort = null;

    const peek = root.querySelector("#outlet-side-peek");
    const container = root.querySelector("[data-lens-root]");
    if (!peek || !container) return;

    peekAbort = new AbortController();
    const { signal } = peekAbort;

    const backdrop = root.querySelector("[data-peek-backdrop]");
    const closeBtn = peek.querySelector("[data-peek-close]");
    const prevBtn = peek.querySelector("[data-peek-prev]");
    const nextBtn = peek.querySelector("[data-peek-next]");
    const posEl = peek.querySelector("[data-peek-pos]");
    const copyBtn = peek.querySelector("[data-peek-copy]");
    const copyStatus = peek.querySelector("#peek-copy-status");
    const peekBody = peek.querySelector(".peek-body");
    const sheets = [...peek.querySelectorAll("[data-peek-item]")];
    const switcher = container.querySelector("[data-lens-switch]");
    const searchInput = container.querySelector("#weak-search");

    peek.hidden = false;
    peek.inert = true;
    if (backdrop) backdrop.hidden = false;

    let activeId = null;
    let lastTrigger = null;
    let statusTimer;
    let iconTimer;

    const getActiveLensKey = () => switcher?.querySelector("input:checked")?.value || "pct";
    const getActivePanel = () =>
      [...container.querySelectorAll("[data-lens-panel]")].find((p) => !p.hidden) ||
      container.querySelector("[data-lens-panel]");
    const getVisibleRows = () => {
      const table = getActivePanel()?.querySelector("table.data");
      if (!table?.tBodies[0]) return [];
      return [...table.tBodies[0].rows].filter((r) => !r.hidden && !r.classList.contains("empty-row"));
    };

    const clearCopyFeedback = () => {
      clearTimeout(statusTimer);
      clearTimeout(iconTimer);
      if (copyStatus) {
        copyStatus.textContent = "";
        copyStatus.classList.remove("ok");
      }
      if (copyBtn) delete copyBtn.dataset.copied;
    };

    const mqCompactPos = window.matchMedia("(max-width: 380px)");

    const syncPeekMeta = () => {
      if (!activeId) return;
      const lensKey = getActiveLensKey();
      const lensTitle = lensKey === "idr" ? "Kehilangan Rp" : "Kemerosotan %";
      const activePanel = getActivePanel();
      const visibleRows = getVisibleRows();
      const idx = visibleRows.findIndex((r) => r.dataset.peekRow === activeId);

      container.querySelectorAll("tr[data-peek-row]").forEach((row) => {
        const isCurrent = activePanel?.contains(row) && row.dataset.peekRow === activeId;
        row.classList.toggle("is-peeked", Boolean(isCurrent));
      });
      container.querySelectorAll("[data-peek-open]").forEach((btn) => {
        const isCurrent = activePanel?.contains(btn) && btn.dataset.peekOpen === activeId;
        btn.setAttribute("aria-expanded", String(Boolean(isCurrent)));
      });

      const activeSheet = sheets.find((s) => s.dataset.peekItem === activeId);
      const rankTag = activeSheet?.querySelector("[data-peek-rank-tag]");
      if (idx >= 0) {
        if (posEl) {
          posEl.textContent = mqCompactPos.matches
            ? `${idx + 1} / ${visibleRows.length}`
            : `${idx + 1} dari ${visibleRows.length} outlet`;
        }
        if (prevBtn) prevBtn.disabled = idx <= 0;
        if (nextBtn) nextBtn.disabled = idx >= visibleRows.length - 1;
        if (rankTag) rankTag.textContent = `Peringkat #${idx + 1} ${lensTitle}`;
      } else {
        if (posEl) posEl.textContent = `${visibleRows.length} outlet`;
        if (prevBtn) prevBtn.disabled = true;
        if (nextBtn) nextBtn.disabled = visibleRows.length === 0;
        if (rankTag) rankTag.textContent = `Evaluasi ${lensTitle}`;
      }
    };

    mqCompactPos.addEventListener("change", () => { if (activeId) syncPeekMeta(); }, { signal });

    const closePeek = ({ restoreFocus = false } = {}) => {
      if (!activeId) return;
      activeId = null;
      delete peek.dataset.open;
      peek.inert = true;
      if (backdrop) delete backdrop.dataset.open;
      clearCopyFeedback();
      container.querySelectorAll("tr.is-peeked").forEach((r) => r.classList.remove("is-peeked"));
      container.querySelectorAll("[data-peek-open]").forEach((b) => b.setAttribute("aria-expanded", "false"));
      if (restoreFocus && lastTrigger?.isConnected) {
        lastTrigger.focus({ preventScroll: true });
      }
    };

    const openPeek = (outletId, { trigger = null, moveFocus = false } = {}) => {
      const targetSheet = sheets.find((s) => s.dataset.peekItem === outletId);
      if (!targetSheet) return;
      const wasOpen = Boolean(activeId);
      activeId = outletId;
      if (trigger) lastTrigger = trigger;

      sheets.forEach((s) => { s.hidden = s !== targetSheet; });
      const skuSec = targetSheet.querySelector("[data-sku-section]");
      if (skuSec) {
        skuSec.querySelectorAll("[data-sku-filter]").forEach((t) => {
          const isAll = t.dataset.skuFilter === "all";
          t.classList.toggle("is-active", isAll);
          t.setAttribute("aria-pressed", String(isAll));
        });
        skuSec.querySelectorAll("[data-sku-group]").forEach((r) => { r.hidden = false; });
        const emptyEl = skuSec.querySelector("[data-sku-empty]");
        if (emptyEl) emptyEl.hidden = true;
      }
      if (peekBody) peekBody.scrollTop = 0;
      clearCopyFeedback();

      peek.dataset.open = "true";
      peek.inert = false;
      if (backdrop) backdrop.dataset.open = "true";
      syncPeekMeta();

      if (moveFocus && !wasOpen) {
        closeBtn?.focus({ preventScroll: true });
      }
    };

    const stepRow = (delta) => {
      if (!activeId) return;
      const visibleRows = getVisibleRows();
      if (!visibleRows.length) return;
      const curIdx = visibleRows.findIndex((r) => r.dataset.peekRow === activeId);
      const nextIdx = curIdx < 0 ? 0 : curIdx + delta;
      if (nextIdx < 0 || nextIdx >= visibleRows.length) return;
      const targetRow = visibleRows[nextIdx];
      const nextId = targetRow.dataset.peekRow;
      const nextTrigger = targetRow.querySelector("[data-peek-open]");
      openPeek(nextId, { trigger: nextTrigger, moveFocus: false });
      targetRow.scrollIntoView({ block: "nearest", behavior: "instant" });
    };

    container.querySelectorAll("[data-peek-open]").forEach((btn) => {
      btn.addEventListener("click", (event) => {
        const id = btn.dataset.peekOpen;
        if (activeId === id && peek.dataset.open === "true") {
          closePeek({ restoreFocus: event.detail === 0 });
        } else {
          openPeek(id, { trigger: btn, moveFocus: event.detail === 0 });
        }
      });
    });

    closeBtn?.addEventListener("click", () => closePeek({ restoreFocus: true }));
    backdrop?.addEventListener("click", () => closePeek({ restoreFocus: false }));
    prevBtn?.addEventListener("click", () => stepRow(-1));
    nextBtn?.addEventListener("click", () => stepRow(1));

    peek.querySelectorAll("[data-sku-section]").forEach((sec) => {
      const tabs = [...sec.querySelectorAll("[data-sku-filter]")];
      const skuRows = [...sec.querySelectorAll("[data-sku-group]")];
      const emptyEl = sec.querySelector("[data-sku-empty]");
      tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          const mode = tab.dataset.skuFilter || "all";
          tabs.forEach((t) => {
            const active = t === tab;
            t.classList.toggle("is-active", active);
            t.setAttribute("aria-pressed", String(active));
          });
          let shown = 0;
          skuRows.forEach((row) => {
            const visible = mode === "all" || row.dataset.skuGroup === mode;
            row.hidden = !visible;
            if (visible) shown += 1;
          });
          if (emptyEl) emptyEl.hidden = shown > 0;
        });
      });
    });

    copyBtn?.addEventListener("click", async () => {
      const activeSheet = sheets.find((s) => s.dataset.peekItem === activeId);
      const src = activeSheet?.querySelector("[data-peek-copy-source]");
      const payload = src?.textContent?.trim();
      if (!payload) return;
      const announce = (msg, ok) => {
        if (copyStatus) {
          copyStatus.textContent = msg;
          copyStatus.classList.toggle("ok", ok);
          clearTimeout(statusTimer);
          statusTimer = setTimeout(() => { copyStatus.textContent = ""; copyStatus.classList.remove("ok"); }, 4000);
        }
        if (ok) {
          copyBtn.dataset.copied = "true";
          clearTimeout(iconTimer);
          iconTimer = setTimeout(() => { delete copyBtn.dataset.copied; }, 1800);
        }
      };
      try {
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(payload);
        } else {
          const temp = document.createElement("textarea");
          temp.value = payload;
          temp.setAttribute("readonly", "");
          temp.style.position = "fixed";
          temp.style.opacity = "0";
          document.body.appendChild(temp);
          temp.select();
          const ok = document.execCommand("copy");
          temp.remove();
          if (!ok) throw new Error("copy failed");
        }
        announce("Tersalin.", true);
      } catch {
        announce("Gagal menyalin.", false);
      }
    });

    switcher?.addEventListener("change", () => {
      if (!activeId) return;
      const inNewLens = getActivePanel()?.querySelector(`tr[data-peek-row="${CSS.escape(activeId)}"]`);
      if (inNewLens) {
        lastTrigger = inNewLens.querySelector("[data-peek-open]") || lastTrigger;
        syncPeekMeta();
      } else {
        closePeek({ restoreFocus: false });
      }
    });

    searchInput?.addEventListener("input", () => { if (activeId) syncPeekMeta(); });
    container.querySelectorAll("[data-weak-reset]").forEach((btn) => {
      btn.addEventListener("click", () => { if (activeId) requestAnimationFrame(syncPeekMeta); });
    });
    container.querySelectorAll("table.sortable").forEach((tbl) => {
      tbl.addEventListener("sorted", () => { if (activeId) syncPeekMeta(); });
    });

    document.addEventListener(
      "keydown",
      (event) => {
        if (!activeId) return;
        const openDialog = document.querySelector("dialog[open]");
        if (openDialog) return;
        if (event.key === "Escape") {
          event.preventDefault();
          closePeek({ restoreFocus: true });
          return;
        }
        const tag = document.activeElement?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
        if (event.key === "ArrowDown") {
          event.preventDefault();
          stepRow(1);
        } else if (event.key === "ArrowUp") {
          event.preventDefault();
          stepRow(-1);
        }
      },
      { signal }
    );

    document.addEventListener(
      "click",
      (event) => {
        if (!activeId) return;
        if (
          event.target.closest(
            "#outlet-side-peek, [data-peek-open], .sort-btn, [data-lens-switch], [data-weak-toolbar], [data-weak-reset], .upload-dialog"
          )
        ) {
          return;
        }
        closePeek({ restoreFocus: false });
      },
      { signal }
    );
  }

  function initPage(root) {
    initCopy(root);
    initSortable(root);
    initOutletTable(root);
    initQuickTables(root);
    initLensSwitch(root);
    initSidePeek(root);
    initSegmented(root);
    initViewSwitch(root);
  }

  // ---------------------------------------------------------------- skeletons (matched to quiet hairline layout)
  const sk = (cls) => `<span class="sk ${cls}"></span>`;
  const skBlock = (inner) => `<div class="sk-block">${inner}</div>`;
  const skHero = () => `<div class="skeleton-head">${sk("sk-eyebrow")}${sk("sk-title")}${sk("sk-line")}</div>`;
  const skRows = (n) => Array.from({ length: n }, () => sk("sk-row")).join("");
  const skStatStrip = () =>
    `<div class="sk-strip">` +
    Array.from({ length: 4 }, () => `<div class="sk-stat">${sk("sk-line short")}${sk("sk-big")}${sk("sk-line")}</div>`).join("") +
    `</div>`;

  const SKELETONS = {
    "/": () =>
      skHero() +
      `<div class="stack">` +
      skStatStrip() +
      `<div class="grid-split">${skBlock(sk("sk-line short") + sk("sk-area"))}${skBlock(sk("sk-line short") + skRows(5))}</div>` +
      skBlock(sk("sk-line short") + skRows(6)) +
      `</div>`,
    "/wilayah-merek": () =>
      skHero() +
      `<div class="sk-tabs">${sk("sk-tab")}${sk("sk-tab")}${sk("sk-tab")}${sk("sk-tab")}</div>` +
      `<div class="stack">` +
      skBlock(sk("sk-line short") + skRows(8)) +
      `</div>`,
    "/outlet-terlemah": () =>
      skHero() +
      `<div class="stack">` +
      skBlock(sk("sk-line short") + skRows(5)) +
      `<div class="method-split">${skBlock(sk("sk-line short") + sk("sk-area"))}${skBlock(sk("sk-line short") + skRows(5))}</div>` +
      `</div>`,
  };

  // ---------------------------------------------------------------- sidebar
  const rootEl = document.documentElement;
  const sidebar = document.getElementById("sidebar");
  const backdrop = document.querySelector("[data-sidebar-backdrop]");
  const sidebarToggles = [...document.querySelectorAll("[data-sidebar-toggle]")];
  const insideToggle = document.querySelector("[data-sidebar-inside]");
  const desktopOpenBtn = document.querySelector("[data-sidebar-desktop-open]");
  const mobileOpenBtn = document.querySelector("[data-sidebar-mobile-open]");
  const mqMobile = window.matchMedia("(max-width: 960px)");
  const modKeyLabel = /Mac|iPhone|iPad/i.test(navigator.platform) ? "Cmd" : "Ctrl";

  function syncSidebar() {
    if (!sidebar) return;
    const isMobile = mqMobile.matches;
    const isOpen = isMobile ? rootEl.dataset.mobileNav === "open" : rootEl.dataset.sidebar !== "collapsed";
    sidebar.inert = !isOpen;
    sidebarToggles.forEach((btn) => btn.setAttribute("aria-expanded", String(isOpen)));
    if (insideToggle) insideToggle.title = `Sembunyikan sidebar (${modKeyLabel}+B)`;
    if (desktopOpenBtn) desktopOpenBtn.title = `Tampilkan sidebar (${modKeyLabel}+B)`;
  }

  function closeMobileSidebar({ restoreFocus = false } = {}) {
    if (rootEl.dataset.mobileNav !== "open") return;
    delete rootEl.dataset.mobileNav;
    syncSidebar();
    if (restoreFocus) mobileOpenBtn?.focus({ preventScroll: true });
  }

  function toggleSidebar({ moveFocus = true } = {}) {
    if (!sidebar) return;
    if (mqMobile.matches) {
      const opening = rootEl.dataset.mobileNav !== "open";
      if (opening) rootEl.dataset.mobileNav = "open";
      else delete rootEl.dataset.mobileNav;
      syncSidebar();
      if (moveFocus) (opening ? insideToggle : mobileOpenBtn)?.focus({ preventScroll: true });
      return;
    }
    const collapsing = rootEl.dataset.sidebar !== "collapsed";
    if (collapsing) {
      rootEl.dataset.sidebar = "collapsed";
      try { localStorage.setItem("dk-sidebar", "collapsed"); } catch {}
    } else {
      delete rootEl.dataset.sidebar;
      try { localStorage.setItem("dk-sidebar", "expanded"); } catch {}
    }
    syncSidebar();
    if (moveFocus) (collapsing ? desktopOpenBtn : insideToggle)?.focus({ preventScroll: true });
  }

  if (sidebar) {
    syncSidebar();
    sidebarToggles.forEach((btn) =>
      btn.addEventListener("click", (event) => toggleSidebar({ moveFocus: event.detail === 0 }))
    );
    backdrop?.addEventListener("click", () => closeMobileSidebar({ restoreFocus: true }));
    mqMobile.addEventListener("change", () => {
      delete rootEl.dataset.mobileNav;
      syncSidebar();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && rootEl.dataset.mobileNav === "open") {
        event.preventDefault();
        closeMobileSidebar({ restoreFocus: true });
        return;
      }
      if ((event.ctrlKey || event.metaKey) && !event.shiftKey && !event.altKey && event.key.toLowerCase() === "b") {
        const tag = document.activeElement?.tagName;
        if (tag === "INPUT" || tag === "TEXTAREA" || document.activeElement?.isContentEditable) return;
        event.preventDefault();
        toggleSidebar();
      }
    });
    requestAnimationFrame(() => rootEl.classList.add("sidebar-ready"));
  }

  // ---------------------------------------------------------------- router
  const main = document.getElementById("isi");
  const progress = document.querySelector(".progress");
  let controller = null;

  function setProgress(state) {
    progress.classList.remove("is-active", "is-done");
    if (state === "idle") return;
    void progress.offsetWidth;
    progress.classList.add(state === "start" ? "is-active" : "is-done");
  }

  function updateNav(page) {
    document.querySelectorAll(".sidenav a[data-key]").forEach((link) => {
      if (link.dataset.key === page) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    });
  }

  async function navigate(href, { push = true } = {}) {
    const url = new URL(href, location.href);
    controller?.abort();
    controller = new AbortController();
    const { signal } = controller;

    setProgress("start");
    closeMobileSidebar();
    updateNav(PAGE_KEYS[url.pathname]);
    main.setAttribute("aria-busy", "true");
    main.classList.remove("is-entering");
    main.classList.add("is-leaving");
    const response = fetch(url, { signal, headers: { Accept: "text/html" } });

    await wait(120);
    if (signal.aborted) return;
    main.classList.remove("is-leaving");
    main.innerHTML = (SKELETONS[url.pathname] || SKELETONS["/"])();
    window.scrollTo({ top: 0, behavior: "instant" });
    const shownAt = performance.now();

    let doc;
    try {
      const res = await response;
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      doc = new DOMParser().parseFromString(await res.text(), "text/html");
    } catch (error) {
      if (error.name === "AbortError") return;
      location.assign(url);
      return;
    }
    const next = doc.getElementById("isi");
    if (!next) { location.assign(url); return; }

    await wait(Math.max(0, MIN_SKELETON_MS - (performance.now() - shownAt)));
    if (signal.aborted) return;

    if (push) history.pushState({}, "", url);
    document.title = doc.title;
    main.dataset.page = next.dataset.page;
    main.innerHTML = next.innerHTML;
    updateNav(next.dataset.page);
    main.removeAttribute("aria-busy");
    void main.offsetWidth;
    main.classList.add("is-entering");
    setProgress("done");
    initPage(main);

    const target = url.hash && document.getElementById(decodeURIComponent(url.hash.slice(1)));
    if (target) {
      target.scrollIntoView({ block: "start", behavior: "instant" });
    } else {
      main.querySelector("h1")?.focus({ preventScroll: true });
    }
  }

  document.addEventListener("click", (event) => {
    const link = event.target.closest("a[href]");
    if (!link || event.defaultPrevented || event.button !== 0) return;
    if (event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    if (link.target || link.hasAttribute("download")) return;
    const url = new URL(link.href);
    if (url.origin !== location.origin || !ROUTES.has(url.pathname)) return;
    if (url.pathname === location.pathname && url.search === location.search && url.hash) return;
    event.preventDefault();
    if (url.href === location.href) return;
    navigate(url.href);
  });

  window.addEventListener("popstate", () => navigate(location.href, { push: false }));

  // ---------------------------------------------------------------- csv upload & flash
  const uploadDialog = document.getElementById("upload-dialog");
  const flashWrap = document.getElementById("flash-banner");

  function formatBytes(bytes) {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1).replace(".", ",")} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(2).replace(".", ",")} MB`;
  }

  function showFlashFromSession() {
    if (!flashWrap) return;
    let msg = "";
    try {
      msg = sessionStorage.getItem("dk-flash") || "";
      if (msg) sessionStorage.removeItem("dk-flash");
    } catch {}
    if (!msg) return;
    const textEl = flashWrap.querySelector("[data-flash-text]");
    if (textEl) textEl.textContent = msg;
    flashWrap.hidden = false;

    let remaining = 7000;
    let startedAt = Date.now();
    let timer = setTimeout(() => { flashWrap.hidden = true; }, remaining);

    document.addEventListener("visibilitychange", () => {
      if (flashWrap.hidden) return;
      if (document.hidden) {
        clearTimeout(timer);
        remaining = Math.max(1000, remaining - (Date.now() - startedAt));
      } else {
        startedAt = Date.now();
        timer = setTimeout(() => { flashWrap.hidden = true; }, remaining);
      }
    });
    flashWrap.querySelector("[data-flash-close]")?.addEventListener("click", () => {
      clearTimeout(timer);
      flashWrap.hidden = true;
    });
  }

  async function resetToSampleData() {
    try {
      const res = await fetch("/api/report/reset", {
        method: "POST",
        headers: { Accept: "application/json" },
      });
      const body = await res.json();
      if (res.ok && body.ok) {
        try {
          sessionStorage.setItem("dk-flash", `Kembali menggunakan data sampel bawaan (${body.source} · ${body.period}).`);
        } catch {}
        location.reload();
      }
    } catch {
      location.reload();
    }
  }

  function initUploadDialog() {
    showFlashFromSession();

    document.querySelectorAll("[data-reset-form]").forEach((form) => {
      form.addEventListener("submit", (event) => {
        event.preventDefault();
        resetToSampleData();
      });
    });

    if (!uploadDialog) return;
    const form = uploadDialog.querySelector("[data-upload-form]");
    const input = uploadDialog.querySelector("#csv-file");
    const dropzone = uploadDialog.querySelector("[data-dropzone]");
    const titleEl = uploadDialog.querySelector("[data-dropzone-title]");
    const subEl = uploadDialog.querySelector("[data-dropzone-sub]");
    const errBox = uploadDialog.querySelector("#upload-error");
    const errText = uploadDialog.querySelector("[data-upload-error-text]");
    const submitBtn = uploadDialog.querySelector("[data-upload-submit]");
    const defaultTitle = titleEl.textContent;
    const defaultSub = subEl.textContent;
    const defaultBtnLabel = submitBtn.textContent;
    let openerBtn = null;

    function setError(message) {
      const hasErr = Boolean(message);
      errBox.hidden = !hasErr;
      errText.textContent = message || "";
      dropzone.classList.toggle("is-invalid", hasErr);
      input.setAttribute("aria-invalid", String(hasErr));
    }

    function updateSelectedFile(file) {
      setError("");
      if (!file) {
        dropzone.classList.remove("has-file");
        titleEl.textContent = defaultTitle;
        subEl.textContent = defaultSub;
        return;
      }
      dropzone.classList.add("has-file");
      titleEl.textContent = file.name;
      subEl.textContent = `${formatBytes(file.size)} · Klik untuk mengganti berkas`;
    }

    function openDialog(trigger, { viaKeyboard = false } = {}) {
      openerBtn = trigger || document.activeElement;
      closeMobileSidebar();
      form.reset();
      updateSelectedFile(null);
      if (typeof uploadDialog.showModal === "function") {
        uploadDialog.showModal();
        if (viaKeyboard && !isCoarsePointer()) input.focus({ preventScroll: true });
        else uploadDialog.focus({ preventScroll: true });
      } else {
        uploadDialog.setAttribute("open", "");
      }
    }

    function closeDialog() {
      if (typeof uploadDialog.close === "function" && uploadDialog.open) {
        uploadDialog.close();
      } else {
        uploadDialog.removeAttribute("open");
      }
    }

    document.querySelectorAll("[data-open-upload]").forEach((btn) => {
      btn.addEventListener("click", (event) => openDialog(btn, { viaKeyboard: event.detail === 0 }));
    });
    uploadDialog.querySelectorAll("[data-close-upload]").forEach((btn) => {
      btn.addEventListener("click", closeDialog);
    });
    uploadDialog.addEventListener("click", (event) => {
      if (event.target === uploadDialog) closeDialog();
    });
    uploadDialog.addEventListener("close", () => {
      openerBtn?.focus?.({ preventScroll: true });
    });

    uploadDialog.querySelector("[data-reset-trigger]")?.addEventListener("click", () => {
      resetToSampleData();
    });

    input.addEventListener("change", () => {
      updateSelectedFile(input.files?.[0] || null);
    });

    ["dragenter", "dragover"].forEach((evtName) => {
      dropzone.addEventListener(evtName, (event) => {
        event.preventDefault();
        dropzone.classList.add("is-dragover");
      });
    });
    ["dragleave", "dragend", "drop"].forEach((evtName) => {
      dropzone.addEventListener(evtName, (event) => {
        event.preventDefault();
        dropzone.classList.remove("is-dragover");
      });
    });
    dropzone.addEventListener("drop", (event) => {
      const file = event.dataTransfer?.files?.[0];
      if (!file) return;
      const dt = new DataTransfer();
      dt.items.add(file);
      input.files = dt.files;
      updateSelectedFile(file);
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const file = input.files?.[0];
      if (!file) {
        setError("Pilih berkas CSV terlebih dahulu sebelum melanjutkan.");
        input.focus();
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        setError("Ukuran berkas melebihi batas maksimum 10 MB.");
        return;
      }

      setError("");
      submitBtn.disabled = true;
      submitBtn.textContent = "Memproses…";
      try {
        const fd = new FormData(form);
        const res = await fetch("/api/upload", {
          method: "POST",
          body: fd,
          headers: { Accept: "application/json" },
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok || !body.ok) {
          setError(body.detail || "Gagal memproses berkas CSV. Periksa kembali format kolomnya.");
          return;
        }
        try {
          const rowsFmt = Number(body.clean_rows || 0).toLocaleString("id-ID");
          sessionStorage.setItem(
            "dk-flash",
            `Data diperbarui dari ${body.source} (${body.period} · ${rowsFmt} baris transaksi bersih).`
          );
        } catch {}
        closeDialog();
        location.reload();
      } catch {
        setError("Tidak dapat menghubungi server. Coba lagi beberapa saat.");
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = defaultBtnLabel;
      }
    });
  }

  initUploadDialog();
  initPage(document);
})();

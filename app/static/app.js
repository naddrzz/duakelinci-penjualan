// Dua Kelinci sales dashboard: page behaviour + a small same-origin router.
// Every page is a normal server-rendered page; this script only enhances it.
// Without JavaScript, links do full page loads and tables show in server order.
(() => {
  "use strict";

  const PAGE_KEYS = { "/": "ringkasan", "/wilayah-merek": "wilayah-merek", "/outlet-terlemah": "outlet-terlemah" };
  const ROUTES = new Set(Object.keys(PAGE_KEYS));
  // A skeleton that flashes for a few milliseconds reads as a glitch, so once it is
  // shown it stays at least this long.
  const MIN_SKELETON_MS = 350;
  const collator = new Intl.Collator("id", { sensitivity: "base", numeric: true });
  const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

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
          say("Tersalin. Tinggal tempel di Telegram.", true);
        } catch {
          text.focus();
          text.select();
          say("Tidak bisa menyalin otomatis. Teks sudah dipilih, tekan Ctrl+C.", false);
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
      if (va === null) return 1; // empty values (new outlets) always last
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
    if (!table || !toolbar) return;
    const sortWrap = root.querySelector("[data-outlet-sort]");
    toolbar.hidden = false;
    sortWrap.hidden = false;

    const search = toolbar.querySelector("#outlet-search");
    const region = toolbar.querySelector("#f-region");
    const type = toolbar.querySelector("#f-type");
    const sortSelect = sortWrap.querySelector("#outlet-sort");
    const count = root.querySelector("[data-outlet-count]");
    const resetButtons = [...root.querySelectorAll("[data-outlet-reset]")];
    const lineReset = root.querySelector(".result-info [data-outlet-reset]");
    const emptyRow = table.querySelector(".empty-row");
    const emptyQuery = table.querySelector("[data-empty-query]");
    const rows = [...table.tBodies[0].rows].filter((row) => !row.classList.contains("empty-row"));
    const statusValue = () => toolbar.querySelector('input[name="status"]:checked').value;

    function apply() {
      const query = search.value.trim().toLowerCase();
      const st = statusValue();
      let shown = 0;
      rows.forEach((row) => {
        const match =
          (!query || row.dataset.search.includes(query)) &&
          (!region.value || row.dataset.region === region.value) &&
          (!type.value || row.dataset.type === type.value) &&
          (!st || row.dataset.status.split(" ").includes(st));
        row.hidden = !match;
        if (match) shown += 1;
      });
      const filtered = Boolean(query || region.value || type.value || st);
      emptyRow.hidden = shown > 0;
      emptyQuery.textContent = query ? ` dengan “${search.value.trim()}”` : "";
      count.textContent = filtered ? `Menampilkan ${shown} dari ${rows.length} outlet` : `${rows.length} outlet`;
      lineReset.hidden = !filtered;
    }

    function reset() {
      search.value = "";
      region.value = "";
      type.value = "";
      const all = toolbar.querySelector('input[name="status"][value=""]');
      all.checked = true;
      all.dispatchEvent(new Event("change", { bubbles: true }));
      apply();
      search.focus();
    }

    search.addEventListener("input", apply);
    [region, type].forEach((el) => el.addEventListener("change", apply));
    toolbar.querySelectorAll('input[name="status"]').forEach((el) => el.addEventListener("change", apply));
    resetButtons.forEach((btn) => btn.addEventListener("click", reset));

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

  // ---------------------------------------------------------------- region/brand switch
  function initViewSwitch(root) {
    const form = root.querySelector("[data-view-switch]");
    if (!form) return;
    const select = form.querySelector("select");
    const views = [...root.querySelectorAll("[data-view]")];
    form.addEventListener("submit", (event) => event.preventDefault());
    select.addEventListener("change", () => {
      views.forEach((view) => {
        const active = view.dataset.view === select.value;
        view.hidden = !active;
        if (active) {
          view.classList.remove("is-entering");
          void view.offsetWidth;
          view.classList.add("is-entering");
        }
      });
      const url = new URL(location.href);
      url.searchParams.set("lihat", select.value);
      history.replaceState(history.state, "", url);
    });
  }

  function initPage(root) {
    initCopy(root);
    initSortable(root);
    initOutletTable(root);
    initSegmented(root);
    initViewSwitch(root);
  }

  // ---------------------------------------------------------------- skeletons (matched to clean open-header layout)
  const sk = (cls) => `<span class="sk ${cls}"></span>`;
  const skCard = (inner) => `<div class="sk-card">${inner}</div>`;
  const skHero = () => `<div class="skeleton-head">${sk("sk-title")}${sk("sk-line")}</div>`;
  const skRows = (n) => Array.from({ length: n }, () => sk("sk-row")).join("");
  const skGrid = (cols, cards) =>
    `<div class="sk-grid" style="grid-template-columns: repeat(auto-fit, minmax(min(100%, ${cols}px), 1fr))">${cards}</div>`;
  const kpiCard = () => skCard(sk("sk-line short") + sk("sk-big") + sk("sk-line short"));

  const SKELETONS = {
    "/": () =>
      skHero() +
      `<div class="stack">` +
      skGrid(240, kpiCard().repeat(4)) +
      skGrid(420, skCard(sk("sk-line short") + skRows(4)) + skCard(sk("sk-line short") + skRows(5))) +
      skGrid(420, skCard(sk("sk-line short") + sk("sk-area")) + skCard(sk("sk-line short") + skRows(4))) +
      skCard(sk("sk-line short") + skRows(6)) +
      `</div>`,
    "/wilayah-merek": () =>
      skHero() +
      `<div class="stack">` +
      skGrid(240, kpiCard().repeat(4)) +
      skCard(sk("sk-line short") + sk("sk-row")) +
      skCard(sk("sk-line short") + skRows(7)) +
      `</div>`,
    "/outlet-terlemah": () =>
      skHero() +
      `<div class="stack">` +
      skGrid(420, skCard(sk("sk-line short") + sk("sk-area")) + skCard(sk("sk-line short") + skRows(5))) +
      skGrid(420, skCard(sk("sk-line") + sk("sk-row") + sk("sk-line short")).repeat(4)) +
      `</div>`,
  };

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
    document.querySelectorAll(".topnav a[data-key]").forEach((link) => {
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

  initPage(document);
})();

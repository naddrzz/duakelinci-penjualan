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
    const forms = [...root.querySelectorAll("[data-view-switch]")];
    if (!forms.length) return;
    const views = [...root.querySelectorAll("[data-view]")];
    const selects = forms.map((f) => f.querySelector("select")).filter(Boolean);
    forms.forEach((form) => form.addEventListener("submit", (event) => event.preventDefault()));
    selects.forEach((select) => {
      select.addEventListener("change", () => {
        const nextKey = select.value;
        const wasKeyboard = select.matches(":focus-visible");
        let activeSelect = null;
        views.forEach((view) => {
          const active = view.dataset.view === nextKey;
          view.hidden = !active;
          if (active) {
            activeSelect = view.querySelector("[data-view-switch] select");
            if (activeSelect) activeSelect.value = nextKey;
            view.classList.remove("is-entering");
            void view.offsetWidth;
            view.classList.add("is-entering");
          }
        });
        select.value = nextKey;
        if (wasKeyboard && activeSelect) {
          activeSelect.focus({ preventScroll: true });
        }
        const url = new URL(location.href);
        url.searchParams.set("lihat", nextKey);
        history.replaceState(history.state, "", url);
      });
    });
  }

  // ---------------------------------------------------------------- dual-lens switch on outlet terlemah
  function initLensSwitch(root) {
    const container = root.querySelector("[data-lens-root]");
    const switcher = container?.querySelector("[data-lens-switch]");
    if (!container || !switcher) return;
    const panels = [...container.querySelectorAll("[data-lens-panel]")];
    if (panels.length < 2) return;
    switcher.hidden = false;

    const sync = (animate = false) => {
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
    };
    sync(false);
    switcher.addEventListener("change", () => sync(true));
  }

  function initPage(root) {
    initCopy(root);
    initSortable(root);
    initOutletTable(root);
    initLensSwitch(root);
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
      skCard(sk("sk-line short") + skRows(6)) +
      skGrid(420, skCard(sk("sk-line short") + sk("sk-area")) + skCard(sk("sk-line short") + skRows(5))) +
      skGrid(420, skCard(sk("sk-line short") + skRows(5)).repeat(2)) +
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
        if (viaKeyboard) input.focus({ preventScroll: true });
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

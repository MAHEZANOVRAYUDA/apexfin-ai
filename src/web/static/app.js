/**
 * ApexFin AI - Frontend Controller & Event Stream Client (Zero-AI-Slop Edition)
 * Mengelola Matriks 6 Status UI, SSE Real-Time Stream, dan Slide-over Drawer.
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const dropzone = document.getElementById("dropzone");
  const fileInput = document.getElementById("file-input");
  const docList = document.getElementById("doc-list");
  const queryForm = document.getElementById("query-form");
  const queryInput = document.getElementById("query-input");
  const submitBtn = document.getElementById("submit-btn");
  const contentCanvas = document.getElementById("content-canvas");
  const streamStepper = document.getElementById("stream-stepper");
  const stepperMsg = document.getElementById("stepper-msg");
  const totalChunksStat = document.getElementById("stat-chunks");

  // Drawer Elements
  const drawerBackdrop = document.getElementById("citation-backdrop");
  const citationDrawer = document.getElementById("citation-drawer");
  const drawerCloseBtn = document.getElementById("drawer-close-btn");
  const drawerDocName = document.getElementById("drawer-doc-name");
  const drawerPageNum = document.getElementById("drawer-page-num");
  const drawerContentType = document.getElementById("drawer-content-type");
  const drawerRelScore = document.getElementById("drawer-rel-score");
  const drawerExcerpt = document.getElementById("drawer-excerpt");
  const drawerCopyBtn = document.getElementById("drawer-copy-btn");

  let currentDocumentId = null;
  let lastExecutedQuery = "";
  let activeCitationData = null;

  // 1. Refresh Statistik & Daftar Dokumen
  async function refreshStats() {
    try {
      const res = await fetch("/api/v1/documents/stats");
      if (res.ok) {
        const data = await res.json();
        totalChunksStat.textContent = data.total_indexed_chunks || "0";
      }
    } catch {
      // Fallback offline
    }
  }

  async function refreshDocumentsList() {
    try {
      const res = await fetch("/api/v1/documents/list");
      if (res.ok) {
        const docs = await res.json();
        renderDocumentsList(docs);
      }
    } catch {
      // Fallback offline
    }
  }

  function renderDocumentsList(docs) {
    if (!docs || docs.length === 0) {
      docList.innerHTML = `
        <div style="font-size: 12px; color: var(--text-muted); font-style: italic; padding: 6px 0;">
          Belum ada dokumen yang diunggah. Tarik file PDF atau klik "Muat Sampel" di atas.
        </div>
      `;
      return;
    }

    docList.innerHTML = "";

    // Show active filter banner if a specific document is locked
    if (currentDocumentId) {
      const activeDoc = docs.find((d) => d.document_id === currentDocumentId);
      const banner = document.createElement("div");
      banner.style.cssText =
        "display: flex; justify-content: space-between; align-items: center; background: var(--bg-tertiary); padding: 5px 8px; border-radius: 4px; margin-bottom: 8px; font-size: 11px; border: 1px solid var(--accent-sky-subtle);";
      banner.innerHTML = `
        <span style="color: var(--accent-sky); font-weight: 500; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">Fokus: ${
          activeDoc ? escapeHtml(activeDoc.document_name) : "1 Dokumen"
        }</span>
        <button id="clear-filter-btn" style="background: none; border: none; color: var(--accent-rose); cursor: pointer; font-size: 11px; font-weight: 600; padding: 0 4px;" title="Cari di semua dokumen">✕ Hapus Filter</button>
      `;
      const clearBtn = banner.querySelector("#clear-filter-btn");
      clearBtn.addEventListener("click", () => {
        currentDocumentId = null;
        renderDocumentsList(docs);
      });
      docList.appendChild(banner);
    }
    docs.forEach((doc) => {
      const card = document.createElement("div");
      card.className = "doc-card";
      const isActive = currentDocumentId === doc.document_id;
      if (isActive) card.classList.add("doc-card-active");

      card.innerHTML = `
        <div style="flex: 1; min-width: 0;">
          <div class="doc-name" title="${escapeHtml(doc.document_name)}" style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
            ${escapeHtml(doc.document_name)}
          </div>
          <div class="doc-meta tabular">${doc.total_pages || 1} Halaman • ${doc.total_chunks} Chunks</div>
        </div>
        <button class="btn-subtle" style="font-size: 11px; margin-left: 6px; ${
          isActive ? "border-color: var(--accent-emerald); color: var(--accent-emerald); background: var(--accent-emerald-subtle);" : ""
        }" title="${isActive ? "Pencarian fokus pada dokumen ini" : "Fokuskan pencarian ke dokumen ini"}">
          ${isActive ? "✓ Terpilih" : "Pilih"}
        </button>
      `;

      const btn = card.querySelector("button");
      btn.addEventListener("click", () => {
        if (currentDocumentId === doc.document_id) {
          currentDocumentId = null;
        } else {
          currentDocumentId = doc.document_id;
        }
        renderDocumentsList(docs);
      });

      docList.appendChild(card);
    });
  }

  // Initial load
  refreshStats();
  refreshDocumentsList();

  // Tombol Preload Sampel
  const loadSamplesBtn = document.getElementById("load-samples-btn");
  if (loadSamplesBtn) {
    loadSamplesBtn.addEventListener("click", async () => {
      loadSamplesBtn.disabled = true;
      loadSamplesBtn.textContent = "⏳ Memproses...";
      try {
        const res = await fetch("/api/v1/documents/load-samples", { method: "POST" });
        if (res.ok) {
          await refreshStats();
          await refreshDocumentsList();
        }
      } catch (err) {
        console.error("Gagal memuat sampel dokumen:", err);
      } finally {
        loadSamplesBtn.disabled = false;
        loadSamplesBtn.textContent = "⚡ Muat Sampel";
      }
    });
  }

  // 2. Drag & Drop File Upload
  dropzone.addEventListener("click", () => fileInput.click());
  fileInput.addEventListener("change", (e) => {
    if (e.target.files.length > 0) {
      uploadFile(e.target.files[0]);
    }
  });

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files.length > 0) {
      uploadFile(e.dataTransfer.files[0]);
    }
  });

  async function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showErrorState({
        title: "Format Berkas Tidak Valid",
        detail: "Mohon unggah berkas laporan keuangan berformat PDF resmi (misal: SEC Form 10-K/10-Q).",
      });
      return;
    }

    const formData = new FormData();
    formData.append("file", file);

    setLoadingState(`Mengunggah dan mengurai '${file.name}' dengan coordinate-aware layout...`);

    try {
      const response = await fetch("/api/v1/documents/upload", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        const errJson = await response.json();
        showErrorState(errJson);
        return;
      }

      const result = await response.json();
      currentDocumentId = result.document_id;
      await refreshStats();
      await refreshDocumentsList();

      queryInput.value = `Berapa total pendapatan bersih pada ${result.document_name}?`;
      showEmptyState(`Dokumen '${result.document_name}' berhasil diindeks (${result.total_chunks} chunk, ${result.tables_extracted} tabel terisolasi). Siap dianalisis.`);
    } catch (err) {
      showErrorState({
        title: "Koneksi Layanan Ingestion Gagal",
        detail: err.message || "Gagal berkomunikasi dengan server backend.",
      });
    }
  }

  // 3. Eksekusi Kueri Analisis & Streaming SSE
  function cleanQuery(str) {
    if (!str) return "";
    let s = str.trim();
    if ((s.startsWith('"') && s.endsWith('"')) || (s.startsWith("'") && s.endsWith("'"))) {
      s = s.slice(1, -1).trim();
    } else if (s.startsWith('"') || s.startsWith("'")) {
      s = s.slice(1).trim();
    }
    return s;
  }

  queryForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const rawQuery = queryInput.value.trim();
    const query = cleanQuery(rawQuery);
    if (!query) return;
    executeStreamingQuery(query);
  });

  document.querySelectorAll(".suggestion-btn[data-query]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const q = cleanQuery(btn.dataset.query);
      queryInput.value = q;
      // Auto-reset conflicting filter if template targets a different filing
      if (q.toLowerCase().includes("apple") && currentDocumentId && currentDocumentId.toLowerCase().includes("nvidia")) {
        currentDocumentId = null;
        refreshDocumentsList();
      } else if (q.toLowerCase().includes("nvidia") && currentDocumentId && currentDocumentId.toLowerCase().includes("apple")) {
        currentDocumentId = null;
        refreshDocumentsList();
      }
      executeStreamingQuery(q);
    });
  });

  function executeStreamingQuery(query) {
    const sanitizedQuery = cleanQuery(query);
    lastExecutedQuery = sanitizedQuery;
    submitBtn.disabled = true;

    // Status Optimistik & Stepper
    streamStepper.style.display = "flex";
    stepperMsg.textContent = "Menghubungkan ke mesin Two-Stage Hybrid Retrieval...";
    setLoadingState("Mengeksekusi Pencarian Hibrida Vektor + Leksikal BM25...");

    const streamUrl = `/api/v1/analysis/stream?q=${encodeURIComponent(sanitizedQuery)}${
      currentDocumentId ? `&document_id=${encodeURIComponent(currentDocumentId)}` : ""
    }`;

    const eventSource = new EventSource(streamUrl);
    let streamFinished = false;

    eventSource.addEventListener("status", (e) => {
      try {
        const statusData = JSON.parse(e.data);
        stepperMsg.textContent = translateStatusMessage(statusData.message);
      } catch {
        // Abaikan
      }
    });

    eventSource.addEventListener("result", (e) => {
      try {
        const report = JSON.parse(e.data);
        renderIdealReport(report);
        streamFinished = true;
      } catch (err) {
        showErrorState({
          title: "Galat Schema Parsing",
          detail: "Gagal merender payload laporan berstruktur.",
          raw: e.data,
        });
      }
    });

    eventSource.addEventListener("problem", (e) => {
      streamFinished = true;
      try {
        const problem = JSON.parse(e.data);
        showErrorState(problem);
      } catch {
        showErrorState({
          title: "Galat Pemrosesan Inferensi",
          detail: e.data,
        });
      }
    });

    eventSource.addEventListener("done", () => {
      streamFinished = true;
      eventSource.close();
      submitBtn.disabled = false;
      streamStepper.style.display = "none";
    });

    eventSource.onerror = () => {
      eventSource.close();
      submitBtn.disabled = false;
      streamStepper.style.display = "none";
      if (!streamFinished) {
        showErrorState({
          title: "Koneksi Aliran Terputus",
          detail: "Komunikasi dengan server streaming terputus. Silakan coba kueri kembali.",
        });
      }
    };
  }

  function translateStatusMessage(msg) {
    if (!msg) return "";
    if (msg.includes("dense vector + BM25")) return "Mengeksekusi pencarian vektor FastEmbed + leksikal BM25Plus...";
    if (msg.includes("Cross-Encoder filtered")) return "Cross-Encoder menyaring potongan konteks paling relevan...";
    if (msg.includes("synthesizing structured report")) return "Mesin LLM menyusun laporan terverifikasi...";
    if (msg.includes("Deterministic verbatim")) return "Pemeriksa fakta deterministik memvalidasi keaslian angka...";
    return msg;
  }

  // State 1: Ideal State (Tampilan Laporan Analisis Lengkap)
  function renderIdealReport(report) {
    const confidencePct = Math.round((report.confidence_score || 0) * 100);

    let metricsHtml = "";
    if (report.extracted_metrics && report.extracted_metrics.length > 0) {
      metricsHtml = report.extracted_metrics
        .map(
          (m) => `
        <div class="metric-card">
          <div class="metric-header">
            <span class="metric-name">${escapeHtml(m.name)}</span>
            <span class="metric-period tabular">${escapeHtml(m.period || "Tahunan")}</span>
          </div>
          <div class="metric-value tabular">${escapeHtml(String(m.value))} <span style="font-size: 11px; color: var(--text-muted); font-weight: normal;">${escapeHtml(m.unit || "")}</span></div>
          <div class="metric-context">"${escapeHtml(m.context_sentence || "")}"</div>
        </div>
      `
        )
        .join("");
    } else {
      metricsHtml = `<div style="grid-column: 1 / -1; font-size: 12px; color: var(--text-muted); padding: 8px 0;">Tidak ada metrik kuantitatif terstruktur yang diekstrak untuk kueri spesifik ini.</div>`;
    }

    let citationsHtml = "";
    if (report.citations && report.citations.length > 0) {
      citationsHtml = report.citations
        .map(
          (c, idx) => `
        <tr class="citation-row" data-citation-idx="${idx}">
          <td class="tabular">#${idx + 1}</td>
          <td><strong>${escapeHtml(c.document_name)}</strong></td>
          <td class="tabular">Hal. ${c.page_number} ${c.is_table ? '<span class="brand-badge" style="font-size: 10px; margin-left: 4px;">Tabel</span>' : ""}</td>
          <td class="citation-excerpt">${escapeHtml(c.excerpt)}</td>
          <td class="tabular" style="color: var(--accent-sky); font-weight: 600;">${Math.round(c.relevance_score * 100)}%</td>
        </tr>
      `
        )
        .join("");
    }

    let warningsHtml = "";
    if (report.audit_warnings && report.audit_warnings.length > 0) {
      warningsHtml = `
        <div class="warning-box">
          <div style="font-size: 12px; font-weight: 700; color: #f59e0b; display: flex; align-items: center; gap: 6px;">
            <span>⚠️ Peringatan Audit &amp; Catatan Verifikasi Angka:</span>
          </div>
          ${report.audit_warnings.map((w) => `<div class="warning-item">• ${escapeHtml(w)}</div>`).join("")}
        </div>
      `;
    }

    contentCanvas.innerHTML = `
      <div class="report-view">
        <!-- Ringkasan Eksekutif -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">
              <span>Ringkasan Eksekutif Terverifikasi</span>
              <span class="brand-badge" style="font-size: 10px;">${escapeHtml(report.model_used || "ApexFin Engine")}</span>
            </div>
            <div class="confidence-badge">Tingkat Keyakinan: ${confidencePct}%</div>
          </div>
          <p class="summary-text">${escapeHtml(report.executive_summary)}</p>
        </div>

        <!-- Peringatan Audit jika ada -->
        ${warningsHtml}

        <!-- Matriks Metrik Finansial -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">Matriks Metrik Finansial Kuantitatif</div>
          </div>
          <div class="metrics-grid">
            ${metricsHtml}
          </div>
        </div>

        <!-- Jejak Audit Sumber Bukti -->
        <div class="card">
          <div class="card-header">
            <div class="card-title">Jejak Audit &amp; Sumber Bukti (Klik Baris untuk Membuka Dokumen)</div>
            <span style="font-size: 11px; color: var(--text-muted);">Verbatim Grounded Citation</span>
          </div>
          <div style="overflow-x: auto;">
            <table class="citations-table">
              <thead>
                <tr>
                  <th style="width: 40px;">No</th>
                  <th style="width: 140px;">Dokumen</th>
                  <th style="width: 100px;">Halaman</th>
                  <th>Kutipan Bukti Verbatim</th>
                  <th style="width: 60px;">Skor</th>
                </tr>
              </thead>
              <tbody>
                ${citationsHtml}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    `;

    // Event delegation untuk membuka Citation Drawer tanpa alert()
    const tableBody = contentCanvas.querySelector(".citations-table tbody");
    if (tableBody) {
      tableBody.addEventListener("click", (e) => {
        const row = e.target.closest(".citation-row");
        if (row && report.citations) {
          const idx = parseInt(row.dataset.citationIdx, 10);
          const citation = report.citations[idx];
          if (citation) openCitationDrawer(citation);
        }
      });
    }
  }

  // Slide-over Drawer Logic
  function openCitationDrawer(c) {
    activeCitationData = c;
    drawerDocName.textContent = c.document_name || "Laporan Keuangan";
    drawerPageNum.textContent = `Halaman ${c.page_number || 1}`;
    drawerContentType.textContent = c.is_table ? "Tabel Finansial Atomik" : "Teks Narasi Laporan";
    drawerRelScore.textContent = `${Math.round((c.relevance_score || 1.0) * 100)}%`;
    drawerExcerpt.textContent = c.excerpt || "";

    drawerBackdrop.classList.add("active");
    citationDrawer.classList.add("active");
    citationDrawer.setAttribute("aria-hidden", "false");
    drawerBackdrop.setAttribute("aria-hidden", "false");
  }

  function closeCitationDrawer() {
    drawerBackdrop.classList.remove("active");
    citationDrawer.classList.remove("active");
    citationDrawer.setAttribute("aria-hidden", "true");
    drawerBackdrop.setAttribute("aria-hidden", "true");
  }

  drawerCloseBtn.addEventListener("click", closeCitationDrawer);
  drawerBackdrop.addEventListener("click", closeCitationDrawer);

  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && citationDrawer.classList.contains("active")) {
      closeCitationDrawer();
    }
  });

  drawerCopyBtn.addEventListener("click", async () => {
    if (activeCitationData && activeCitationData.excerpt) {
      try {
        await navigator.clipboard.writeText(activeCitationData.excerpt);
        drawerCopyBtn.textContent = "✓ Berhasil Disalin!";
        setTimeout(() => {
          drawerCopyBtn.textContent = "Salin Teks Bukti";
        }, 2000);
      } catch {
        // Fallback
      }
    }
  });

  // State 2: Empty State
  function showEmptyState(customDesc) {
    contentCanvas.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon-wrap">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" class="empty-svg">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75zM9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625zM16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z" />
          </svg>
        </div>
        <h2 class="empty-title">Intelijen Laporan Keuangan Bebas Halusinasi</h2>
        <p class="empty-desc">
          ${customDesc || "Unggah dokumen PDF laporan keuangan atau pilih template kueri di sebelah kiri untuk menjalankan Two-Stage Hybrid Retrieval dengan verifikasi numerik deterministik."}
        </p>
      </div>
    `;
  }

  // State 3: Loading Skeleton State
  function setLoadingState(message) {
    contentCanvas.innerHTML = `
      <div class="skeleton-container" aria-busy="true">
        <div style="font-size: 12px; color: var(--text-muted); margin-bottom: 4px;">${message}</div>
        <div class="skeleton-box" style="height: 120px;"></div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
          <div class="skeleton-box" style="height: 90px;"></div>
          <div class="skeleton-box" style="height: 90px;"></div>
        </div>
        <div class="skeleton-box" style="height: 180px;"></div>
      </div>
    `;
  }

  // State 4: Error State dengan RFC 7807 problem details terlipat
  function showErrorState(err) {
    submitBtn.disabled = false;
    streamStepper.style.display = "none";

    contentCanvas.innerHTML = `
      <div class="error-state-box">
        <div class="error-title">⚠️ ${escapeHtml(err.title || "Operasi Tidak Berhasil")}</div>
        <div class="error-detail">${escapeHtml(err.detail || "Terjadi kendala saat memproses kueri analitis Anda.")}</div>
        <button class="btn-primary" onclick="window.retryLastQuery()" style="height: 36px; font-size: 12px;">
          ↻ Coba Ulang Kueri
        </button>
        <details style="margin-top: 14px; cursor: pointer;">
          <summary style="font-size: 11px; color: var(--text-muted);">Lihat Rincian Teknis RFC 7807 Problem Details</summary>
          <pre class="error-rfc-details">${escapeHtml(JSON.stringify(err, null, 2))}</pre>
        </details>
      </div>
    `;
  }

  window.retryLastQuery = () => {
    if (lastExecutedQuery) {
      executeStreamingQuery(lastExecutedQuery);
    }
  };

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});

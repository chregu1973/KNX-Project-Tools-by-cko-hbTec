(() => {
    "use strict";

    const form = document.getElementById("labelsForm");
    if (!form) return;

    const byId = id => document.getElementById(id);
    const rows = Array.from(document.querySelectorAll("#labelDeviceTable tr"));
    const checkboxes = Array.from(document.querySelectorAll(".label-device-checkbox"));

    const searchInput = byId("labelDeviceSearch");
    const areaSelect = byId("labelAreaFilter");
    const lineSelect = byId("labelLineFilter");
    const presetSelect = byId("labelPreset");
    const startSelect = byId("startPosition");
    const pdfButton = byId("labelsPdfButton");
    const logoInput = byId("labelLogo");
    const logoPreview = byId("labelPreviewLogo");
    const clearLogoButton = byId("clearLabelLogo");
    let logoObjectUrl = "";

    const dimensionIds = [
        "labelWidth", "labelHeight", "labelCols", "labelRows",
        "marginLeft", "marginTop", "gapX", "gapY"
    ];

    const presets = {
        "avery-3422": {
            width: 70, height: 35, cols: 3, rows: 8,
            marginLeft: 0, marginTop: 8.5, gapX: 0, gapY: 0
        },
        "avery-6122": {
            width: 70, height: 36, cols: 3, rows: 8,
            marginLeft: 0, marginTop: 4.5, gapX: 0, gapY: 0
        },
        "avery-3652": {
            width: 70, height: 42.3, cols: 3, rows: 7,
            marginLeft: 0, marginTop: 0.45, gapX: 0, gapY: 0
        },
        "avery-3653": {
            width: 105, height: 42.3, cols: 2, rows: 7,
            marginLeft: 0, marginTop: 0.45, gapX: 0, gapY: 0
        }
    };

    const numberValue = (id, fallback = 0) => {
        const value = Number.parseFloat(byId(id)?.value);
        return Number.isFinite(value) ? value : fallback;
    };

    const positiveInteger = (id, fallback = 1) => {
        return Math.max(1, Math.floor(numberValue(id, fallback)));
    };

    const canonicalArea = value => {
        const match = String(value || "").match(/(?:^|\D)(\d+)(?:\D|$)/);
        return match ? match[1] : "";
    };

    const canonicalLine = value => {
        const match = String(value || "").match(/(\d+)\.(\d+)/);
        return match ? `${match[1]}.${match[2]}` : "";
    };

    const initialLineOptions = Array.from(lineSelect.options)
        .slice(1)
        .map(option => option.cloneNode(true));

    const updateLineOptions = () => {
        const area = canonicalArea(areaSelect.value);
        const previous = canonicalLine(lineSelect.value);
        const placeholder = lineSelect.options[0].cloneNode(true);

        const options = initialLineOptions
            .filter(option => {
                const line = canonicalLine(option.value || option.textContent);
                return !area || line.startsWith(`${area}.`);
            })
            .map(option => {
                const clone = option.cloneNode(true);
                const line = canonicalLine(clone.value || clone.textContent);
                if (line) clone.value = line;
                return clone;
            });

        lineSelect.replaceChildren(placeholder, ...options);

        if (previous && options.some(option => option.value === previous)) {
            lineSelect.value = previous;
        } else {
            lineSelect.value = "";
        }
    };

    const visibleRows = () => rows.filter(row => !row.hidden);
    const selectedRows = () => rows.filter(row => row.querySelector(".label-device-checkbox")?.checked);

    const filterRows = () => {
        const search = String(searchInput.value || "").trim().toLocaleLowerCase("de-CH");
        const area = canonicalArea(areaSelect.value);
        const line = canonicalLine(lineSelect.value);

        rows.forEach(row => {
            const matchesSearch = !search || String(row.dataset.search || "")
                .toLocaleLowerCase("de-CH")
                .includes(search);
            const matchesArea = !area || row.dataset.area === area;
            const matchesLine = !line || row.dataset.line === line;

            row.hidden = !(matchesSearch && matchesArea && matchesLine);
        });

        updateSummary();
        updateSample();
    };

    const setSelection = mode => {
        const visible = new Set(visibleRows());

        rows.forEach(row => {
            const checkbox = row.querySelector(".label-device-checkbox");
            if (!checkbox) return;

            if (mode === "all") checkbox.checked = true;
            if (mode === "none") checkbox.checked = false;
            if (mode === "filtered") checkbox.checked = visible.has(row);
        });

        updateSummary();
        updateSample();
    };

    const applyPreset = () => {
        const preset = presets[presetSelect.value];
        const custom = !preset;

        dimensionIds.forEach(id => {
            byId(id).readOnly = !custom;
        });

        if (preset) {
            byId("labelWidth").value = preset.width;
            byId("labelHeight").value = preset.height;
            byId("labelCols").value = preset.cols;
            byId("labelRows").value = preset.rows;
            byId("marginLeft").value = preset.marginLeft;
            byId("marginTop").value = preset.marginTop;
            byId("gapX").value = preset.gapX;
            byId("gapY").value = preset.gapY;
        }

        updateStartPositions();
        updateSummary();
    };

    const updateStartPositions = () => {
        const capacity = positiveInteger("labelCols") * positiveInteger("labelRows");
        const oldValue = Math.min(Number(startSelect.value || 1), capacity);

        const fragment = document.createDocumentFragment();
        for (let index = 1; index <= capacity; index += 1) {
            const option = document.createElement("option");
            option.value = String(index);
            option.textContent = index === 1 ? "1 · Neuer Bogen" : `${index} · ${index - 1} Positionen überspringen`;
            fragment.appendChild(option);
        }

        startSelect.replaceChildren(fragment);
        startSelect.value = String(oldValue || 1);
    };

    const validateFormat = () => {
        const width = numberValue("labelWidth");
        const height = numberValue("labelHeight");
        const cols = positiveInteger("labelCols");
        const rowCount = positiveInteger("labelRows");
        const marginLeft = numberValue("marginLeft");
        const marginTop = numberValue("marginTop");
        const gapX = numberValue("gapX");
        const gapY = numberValue("gapY");

        const usedWidth = marginLeft + cols * width + Math.max(0, cols - 1) * gapX;
        const usedHeight = marginTop + rowCount * height + Math.max(0, rowCount - 1) * gapY;
        const validNumbers = [width, height, marginLeft, marginTop, gapX, gapY]
            .every(value => Number.isFinite(value) && value >= 0) && width > 0 && height > 0;
        const fits = validNumbers && usedWidth <= 210.01 && usedHeight <= 297.01;

        const status = byId("labelFormatStatus");
        status.classList.toggle("is-error", !fits);

        if (!validNumbers) {
            status.textContent = "Bitte nur gültige positive Masse eingeben.";
        } else if (!fits) {
            status.textContent = `Format zu gross: ${usedWidth.toFixed(1)} × ${usedHeight.toFixed(1)} mm belegt, A4 hat 210 × 297 mm.`;
        } else {
            status.textContent = `Passt auf A4: ${usedWidth.toFixed(1)} × ${usedHeight.toFixed(1)} mm belegt.`;
        }

        return fits;
    };

    const calculatePages = selected => {
        const capacity = positiveInteger("labelCols") * positiveInteger("labelRows");
        const start = Math.max(1, Number(startSelect.value || 1));
        const firstPageCapacity = Math.max(0, capacity - (start - 1));

        if (selected <= 0) return 0;
        if (selected <= firstPageCapacity) return 1;
        return 1 + Math.ceil((selected - firstPageCapacity) / capacity);
    };

    const updateSheetPreview = selected => {
        const preview = byId("labelSheetPreview");
        const cols = positiveInteger("labelCols");
        const rowCount = positiveInteger("labelRows");
        const capacity = cols * rowCount;
        const start = Math.max(1, Number(startSelect.value || 1));
        const maxPreviewCells = 60;
        const shownCapacity = Math.min(capacity, maxPreviewCells);

        preview.style.setProperty("--sheet-cols", String(Math.min(cols, 10)));
        preview.replaceChildren();

        for (let index = 0; index < shownCapacity; index += 1) {
            const cell = document.createElement("span");
            const position = index + 1;

            if (position < start) cell.className = "is-skipped";
            else if (position < start + selected) cell.className = "is-filled";

            preview.appendChild(cell);
        }

        if (capacity > maxPreviewCells) {
            preview.dataset.more = `+${capacity - maxPreviewCells}`;
        } else {
            delete preview.dataset.more;
        }
    };

    const updateSummary = () => {
        const selected = selectedRows().length;
        const visible = visibleRows().length;
        const capacity = positiveInteger("labelCols") * positiveInteger("labelRows");
        const start = Math.max(1, Number(startSelect.value || 1));
        const firstPageFree = Math.max(0, capacity - (start - 1));
        const pages = calculatePages(selected);
        const formatValid = validateFormat();

        byId("labelTotalCount").textContent = rows.length;
        byId("labelVisibleCount").textContent = visible;
        byId("labelSelectedCount").textContent = selected;
        byId("labelPerSheetCount").textContent = capacity;
        byId("labelCapacityBadge").textContent = `${capacity} / Bogen`;
        byId("labelFirstPageFree").textContent = firstPageFree;
        byId("labelPageCount").textContent = pages;

        const hint = byId("labelsPdfHint");
        if (!formatValid) hint.textContent = "Bogenformat korrigieren";
        else if (!selected) hint.textContent = "Zuerst Geräte auswählen";
        else hint.textContent = `${selected} Etiketten · ${pages} ${pages === 1 ? "Bogen" : "Bögen"}`;

        pdfButton.disabled = !formatValid || selected === 0;
        updateSheetPreview(selected);
    };

    const previewFields = {
        location: byId("labelPreviewLocation"),
        address: byId("labelPreviewAddress"),
        room: byId("labelPreviewRoom"),
        description: byId("labelPreviewDescription")
    };

    const updateSample = () => {
        const selectedVisible = visibleRows().find(row => row.querySelector(".label-device-checkbox")?.checked);
        const sampleRow = selectedVisible || selectedRows()[0] || visibleRows()[0] || rows[0];

        if (sampleRow) {
            previewFields.location.textContent = sampleRow.dataset.location || "Standortpfad";
            previewFields.address.textContent = sampleRow.dataset.address || "1.1.1";
            previewFields.room.textContent = sampleRow.dataset.room || "Raum / Verteiler";
            previewFields.description.textContent = sampleRow.dataset.description || "Gerätebeschreibung";
        }

        document.querySelectorAll(".label-content-toggle").forEach(toggle => {
            const field = previewFields[toggle.dataset.preview];
            if (field) field.hidden = !toggle.checked;
        });
    };

    const clearLogoPreview = () => {
        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
        logoObjectUrl = "";
        logoInput.value = "";
        logoPreview.removeAttribute("src");
        logoPreview.hidden = true;
        clearLogoButton.hidden = true;
    };

    const updateLogoPreview = () => {
        const file = logoInput.files?.[0];

        if (!file) {
            clearLogoPreview();
            return;
        }

        const supportedMime = /^image\/(png|jpeg)$/i.test(file.type || "");
        const supportedExtension = /\.(png|jpe?g)$/i.test(file.name || "");

        if ((!supportedMime && !supportedExtension) || file.size > 2 * 1024 * 1024) {
            window.alert("Bitte ein PNG- oder JPG-Logo mit maximal 2 MB auswählen.");
            clearLogoPreview();
            return;
        }

        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
        logoObjectUrl = URL.createObjectURL(file);
        logoPreview.src = logoObjectUrl;
        logoPreview.hidden = false;
        clearLogoButton.hidden = false;
    };

    searchInput.addEventListener("input", filterRows);

    areaSelect.addEventListener("change", () => {
        updateLineOptions();
        filterRows();
    });

    lineSelect.addEventListener("change", filterRows);
    presetSelect.addEventListener("change", applyPreset);
    startSelect.addEventListener("change", updateSummary);

    dimensionIds.forEach(id => {
        byId(id).addEventListener("input", () => {
            if (id === "labelCols" || id === "labelRows") updateStartPositions();
            updateSummary();
        });
    });

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener("change", () => {
            updateSummary();
            updateSample();
        });
    });

    document.querySelectorAll(".label-content-toggle").forEach(toggle => {
        toggle.addEventListener("change", updateSample);
    });

    logoInput.addEventListener("change", updateLogoPreview);
    clearLogoButton.addEventListener("click", clearLogoPreview);
    window.addEventListener("beforeunload", () => {
        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
    });

    byId("selectFilteredLabels").addEventListener("click", () => setSelection("filtered"));
    byId("selectAllLabels").addEventListener("click", () => setSelection("all"));
    byId("clearLabelSelection").addEventListener("click", () => setSelection("none"));

    form.addEventListener("submit", event => {
        if (!validateFormat() || selectedRows().length === 0) {
            event.preventDefault();
            updateSummary();
        }
    });

    updateLineOptions();
    applyPreset();
    filterRows();
    updateSample();
})();

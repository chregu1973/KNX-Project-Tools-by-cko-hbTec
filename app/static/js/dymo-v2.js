(() => {
    "use strict";

    const table = document.getElementById("dymoDeviceTable");
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tr"));
    const checkboxes = Array.from(document.querySelectorAll(".dymo-device-checkbox"));
    const search = document.getElementById("dymoDeviceSearch");
    const area = document.getElementById("dymoAreaFilter");
    const line = document.getElementById("dymoLineFilter");
    const visibleCount = document.getElementById("dymoVisibleCount");
    const selectedCount = document.getElementById("dymoSelectedCount");
    const exportStatus = document.getElementById("dymoExportStatus");
    const csvButton = document.getElementById("dymoCsvButton");
    const pdfButton = document.getElementById("dymoPdfButton");
    const previewLabel = document.getElementById("dymoPreviewLabel");
    const previewLocation = document.getElementById("dymoPreviewLocation");
    const previewAddress = document.getElementById("dymoPreviewAddress");
    const previewRoom = document.getElementById("dymoPreviewRoom");
    const previewDescription = document.getElementById("dymoPreviewDescription");
    const logoInput = document.getElementById("dymoLogo");
    const logoPreview = document.getElementById("dymoPreviewLogo");
    const logoClear = document.getElementById("dymoLogoClear");
    const contentToggles = Array.from(document.querySelectorAll(".dymo-content-toggle"));

    let logoObjectUrl = "";

    function visibleRows() {
        return rows.filter(row => !row.hidden);
    }

    function selectedCheckboxes() {
        return checkboxes.filter(checkbox => checkbox.checked);
    }

    function sampleRow() {
        const selected = selectedCheckboxes()[0];
        if (selected) return selected.closest("tr");
        return visibleRows()[0] || rows[0] || null;
    }

    function updateLineOptions() {
        const selectedArea = area.value;

        Array.from(line.options).forEach((option, index) => {
            if (index === 0) return;
            const matches = !selectedArea || option.dataset.area === selectedArea;
            option.hidden = !matches;
            option.disabled = !matches;
        });

        const current = line.selectedOptions[0];
        if (current && current.disabled) line.value = "";
    }

    function filterRows() {
        const term = search.value.trim().toLocaleLowerCase("de-CH");
        const selectedArea = area.value;
        const selectedLine = line.value;

        rows.forEach(row => {
            const matchesSearch = !term || row.dataset.search.toLocaleLowerCase("de-CH").includes(term);
            const matchesArea = !selectedArea || row.dataset.area === selectedArea;
            const matchesLine = !selectedLine || row.dataset.line === selectedLine;
            row.hidden = !(matchesSearch && matchesArea && matchesLine);
        });

        updateSummary();
    }

    function updateContentVisibility() {
        contentToggles.forEach(toggle => {
            const target = document.getElementById(
                `dymoPreview${toggle.dataset.preview.charAt(0).toUpperCase()}${toggle.dataset.preview.slice(1)}`
            );
            if (target) target.hidden = !toggle.checked;
        });
    }

    function updatePreview() {
        const row = sampleRow();

        previewLocation.textContent = row?.dataset.location || "Standort / Bereich / Linie";
        previewAddress.textContent = row?.dataset.address || "1.1.1";
        previewRoom.textContent = row?.dataset.room || "Raum / Verteiler";
        previewDescription.textContent = row?.dataset.description || "Gerätebeschreibung";

        updateContentVisibility();
    }

    function updateSummary() {
        const selected = selectedCheckboxes().length;
        const visible = visibleRows().length;

        visibleCount.textContent = visible;
        selectedCount.textContent = selected;
        csvButton.disabled = selected === 0;
        pdfButton.disabled = selected === 0;

        exportStatus.textContent = selected === 0
            ? "Bitte mindestens ein Gerät auswählen."
            : `${selected} ${selected === 1 ? "Etikett ist" : "Etiketten sind"} für beide Downloads vorbereitet.`;

        updatePreview();
    }

    function clearLogo() {
        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
        logoObjectUrl = "";
        logoInput.value = "";
        logoPreview.removeAttribute("src");
        logoPreview.hidden = true;
        logoClear.hidden = true;
        previewLabel.classList.remove("has-logo");
    }

    function updateLogoPreview() {
        const file = logoInput.files?.[0];

        if (!file) {
            clearLogo();
            return;
        }

        if (!/^image\/(png|jpeg)$/.test(file.type) || file.size > 2 * 1024 * 1024) {
            clearLogo();
            exportStatus.textContent = "Bitte ein PNG- oder JPG-Logo mit maximal 2 MB auswählen.";
            return;
        }

        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
        logoObjectUrl = URL.createObjectURL(file);
        logoPreview.src = logoObjectUrl;
        logoPreview.hidden = false;
        logoClear.hidden = false;
        previewLabel.classList.add("has-logo");
    }

    area.addEventListener("change", () => {
        updateLineOptions();
        filterRows();
    });

    line.addEventListener("change", filterRows);
    search.addEventListener("input", filterRows);
    logoInput.addEventListener("change", updateLogoPreview);
    logoClear.addEventListener("click", clearLogo);

    contentToggles.forEach(toggle => toggle.addEventListener("change", updateContentVisibility));
    checkboxes.forEach(checkbox => checkbox.addEventListener("change", updateSummary));

    document.getElementById("dymoSelectVisible").addEventListener("click", () => {
        visibleRows().forEach(row => {
            row.querySelector(".dymo-device-checkbox").checked = true;
        });
        updateSummary();
    });

    document.getElementById("dymoSelectAll").addEventListener("click", () => {
        checkboxes.forEach(checkbox => { checkbox.checked = true; });
        updateSummary();
    });

    document.getElementById("dymoClearAll").addEventListener("click", () => {
        checkboxes.forEach(checkbox => { checkbox.checked = false; });
        updateSummary();
    });

    document.getElementById("dymoForm").addEventListener("submit", event => {
        if (selectedCheckboxes().length === 0) {
            event.preventDefault();
            exportStatus.textContent = "Bitte zuerst mindestens ein Gerät auswählen.";
        }
    });

    window.addEventListener("beforeunload", () => {
        if (logoObjectUrl) URL.revokeObjectURL(logoObjectUrl);
    });

    updateLineOptions();
    filterRows();
})();

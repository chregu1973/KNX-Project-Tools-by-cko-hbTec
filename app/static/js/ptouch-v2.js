(() => {
    "use strict";

    const table = document.getElementById("ptouchDeviceTable");
    if (!table) return;

    const rows = Array.from(table.querySelectorAll("tr"));
    const checkboxes = Array.from(document.querySelectorAll(".ptouch-device-checkbox"));
    const search = document.getElementById("ptouchDeviceSearch");
    const area = document.getElementById("ptouchAreaFilter");
    const line = document.getElementById("ptouchLineFilter");
    const prefix = document.getElementById("ptouchPrefix");
    const date = document.getElementById("ptouchDate");
    const previewHeader = document.getElementById("ptouchPreviewHeader");
    const previewAddress = document.getElementById("ptouchPreviewAddress");
    const visibleCount = document.getElementById("ptouchVisibleCount");
    const selectedCount = document.getElementById("ptouchSelectedCount");
    const exportStatus = document.getElementById("ptouchExportStatus");
    const csvButton = document.getElementById("ptouchCsvButton");
    const projectButton = document.getElementById("ptouchProjectButton");

    function visibleRows() {
        return rows.filter(row => !row.hidden);
    }

    function selectedCheckboxes() {
        return checkboxes.filter(checkbox => checkbox.checked);
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

    function firstSelectedAddress() {
        const selected = selectedCheckboxes()[0];
        if (selected) return selected.value;

        const firstVisible = visibleRows()[0];
        const fallback = firstVisible && firstVisible.querySelector(".ptouch-device-checkbox");
        return fallback ? fallback.value : "1.1.1";
    }

    function updatePreview() {
        previewHeader.textContent = [prefix.value.trim(), date.value.trim()].filter(Boolean).join(" ") || "Text / Datum";
        previewAddress.textContent = firstSelectedAddress();
    }

    function updateSummary() {
        const selected = selectedCheckboxes().length;
        const visible = visibleRows().length;

        visibleCount.textContent = visible;
        selectedCount.textContent = selected;
        csvButton.disabled = selected === 0;
        projectButton.disabled = selected === 0;

        exportStatus.textContent = selected === 0
            ? "Bitte mindestens ein Gerät auswählen."
            : `${selected} ${selected === 1 ? "Etikett ist" : "Etiketten sind"} für beide Downloads vorbereitet.`;

        updatePreview();
    }

    area.addEventListener("change", () => {
        updateLineOptions();
        filterRows();
    });

    line.addEventListener("change", filterRows);
    search.addEventListener("input", filterRows);
    prefix.addEventListener("input", updatePreview);
    date.addEventListener("input", updatePreview);

    checkboxes.forEach(checkbox => checkbox.addEventListener("change", updateSummary));

    document.getElementById("ptouchSelectVisible").addEventListener("click", () => {
        visibleRows().forEach(row => {
            row.querySelector(".ptouch-device-checkbox").checked = true;
        });
        updateSummary();
    });

    document.getElementById("ptouchSelectAll").addEventListener("click", () => {
        checkboxes.forEach(checkbox => { checkbox.checked = true; });
        updateSummary();
    });

    document.getElementById("ptouchClearAll").addEventListener("click", () => {
        checkboxes.forEach(checkbox => { checkbox.checked = false; });
        updateSummary();
    });

    document.getElementById("ptouchForm").addEventListener("submit", event => {
        if (selectedCheckboxes().length === 0) {
            event.preventDefault();
            exportStatus.textContent = "Bitte zuerst mindestens ein Gerät auswählen.";
        }
    });

    updateLineOptions();
    filterRows();
})();

function filterTable() {

    let input = document.getElementById("search");

    if (!input)
        return;

    let filter = input.value.toUpperCase();

    let table = document.getElementById("deviceTable");

    let rows = table.getElementsByTagName("tr");

    for (let i = 1; i < rows.length; i++) {

        let text = rows[i].innerText.toUpperCase();

        if (text.indexOf(filter) > -1)
            rows[i].style.display = "";
        else
            rows[i].style.display = "none";
    }
}
function updateLabelPreview() {
    const preview = document.getElementById("a4Preview");
    if (!preview) return;

    const cols = document.getElementById("labelCols").value || 3;
    const rows = document.getElementById("labelRows").value || 8;
    const width = parseFloat(document.getElementById("labelWidth").value || 70);
    const height = parseFloat(document.getElementById("labelHeight").value || 35);

    const marginLeft = parseFloat(document.getElementById("marginLeft").value || 0);
    const marginTop = parseFloat(document.getElementById("marginTop").value || 8); 

    preview.style.gridTemplateColumns = `repeat(${cols}, ${width}mm)`;
    preview.style.gridAutoRows = `${height}mm`;

    preview.style.paddingLeft = `${marginLeft}mm`;
    preview.style.paddingTop = `${marginTop}mm`;

}

document.addEventListener("input", updateLabelPreview);
document.addEventListener("DOMContentLoaded", updateLabelPreview);

function showLoading() {
    const button = document.getElementById("loadButton");
    const box = document.getElementById("loadingBox");

    if (button) {
        button.disabled = true;
        button.innerText = "Projekt wird geladen...";
    }

    if (box) {
        box.style.display = "flex";
    }
}
// ===========================
// Verpackungsetiketten
// ===========================

function getLabelRows() {
    return Array.from(document.querySelectorAll("#labelDeviceTable tr"));
}

function updateStartPosition() {

    const cols = Number(document.getElementById("labelCols").value);
    const rows = Number(document.getElementById("labelRows").value);

    const select = document.getElementById("startPosition");

    if (!select) return;

    const old = select.value;

    select.innerHTML = "";

    for (let i = 1; i <= cols * rows; i++) {

        const option = document.createElement("option");

        option.value = i;
        option.text = i;

        if (String(i) === old)
            option.selected = true;

        select.appendChild(option);
    }

    if (!select.value)
        select.value = 1;

    updateLabelSummary();
}


function filterLabelDevices() {

    const search =
        document
            .getElementById("labelDeviceSearch")
            .value
            .toLowerCase();

    const area =
        document
            .getElementById("labelAreaFilter")
            .value;

    const line =
        document
            .getElementById("labelLineFilter")
            .value;

    getLabelRows().forEach(row => {

        let visible = true;

        if (search &&
            !row.dataset.search.toLowerCase().includes(search))
            visible = false;

        if (area &&
            row.dataset.area !== area)
            visible = false;

        if (line &&
            row.dataset.line !== line)
            visible = false;

        row.style.display = visible ? "" : "none";

        if (!visible) {
            const checkbox = row.querySelector(".label-device-checkbox");

            if (checkbox) {
                checkbox.checked = false;
            }
        }

    });

    updateLabelSummary();
}


function selectAllLabelDevices() {

    document
        .querySelectorAll(".label-device-checkbox")
        .forEach(cb => cb.checked = true);

    updateLabelSummary();
}


function clearAllLabelDevices() {

    document
        .querySelectorAll(".label-device-checkbox")
        .forEach(cb => cb.checked = false);

    updateLabelSummary();
}


function selectVisibleLabelDevices() {

    clearAllLabelDevices();

    getLabelRows().forEach(row => {

        if (row.style.display !== "none")
            row.querySelector("input").checked = true;

    });

    updateLabelSummary();
}


function updateLabelSummary() {

    const total =
        getLabelRows().length;

    const selected =
        document.querySelectorAll(".label-device-checkbox:checked").length;

    document.getElementById("labelTotalCount").textContent =
        total;

    document.getElementById("labelSelectedCount").textContent =
        selected;

    const cols =
        Number(document.getElementById("labelCols").value);

    const rows =
        Number(document.getElementById("labelRows").value);

    const start =
        Number(document.getElementById("startPosition").value);

    const firstPage =
        cols * rows - (start - 1);

    let pages = 0;

    if (selected > 0) {

        if (selected <= firstPage)
            pages = 1;

        else
            pages =
                1 +
                Math.ceil(
                    (selected - firstPage) /
                    (cols * rows)
                );

    }

    document.getElementById("labelPageCount").textContent =
        pages;
}


document.addEventListener("DOMContentLoaded", () => {

    if (!document.getElementById("labelDeviceSearch"))
        return;

    updateStartPosition();

    document
        .getElementById("labelDeviceSearch")
        .addEventListener("input", filterLabelDevices);

    document
        .getElementById("labelAreaFilter")
        .addEventListener("change", filterLabelDevices);

    document
        .getElementById("labelLineFilter")
        .addEventListener("change", filterLabelDevices);

    document
        .querySelectorAll(".label-device-checkbox")
        .forEach(cb =>
            cb.addEventListener("change", updateLabelSummary)
        );

    document
        .getElementById("labelCols")
        .addEventListener("input", updateStartPosition);

    document
        .getElementById("labelRows")
        .addEventListener("input", updateStartPosition);

    document
        .getElementById("startPosition")
        .addEventListener("change", updateLabelSummary);

    updateLabelSummary();

});

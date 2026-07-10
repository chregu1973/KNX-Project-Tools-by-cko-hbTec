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

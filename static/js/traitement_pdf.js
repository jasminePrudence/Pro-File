document.querySelector('input[name="file"]').addEventListener('change', function(event) {
    const file = event.target.files[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = function() {
        const typedArray = new Uint8Array(this.result);
        pdfjsLib.getDocument(typedArray).promise.then(pdf => {
            let textArray = [];
            let pagesProcessed = 0;

            for (let pageNum = 1; pageNum <= pdf.numPages; pageNum++) {
                pdf.getPage(pageNum).then(page => {
                    page.getTextContent().then(textContent => {
                        let text = textContent.items.map(item => item.str).join(" ");
                        textArray.push(...text.split("\n")); // Diviser par lignes

                        pagesProcessed++;
                        if (pagesProcessed === pdf.numPages) {
                            // Une fois toutes les pages chargées, afficher les 5 dernières lignes
                            let lastLines = textArray.slice(-5).join("<br>");
                            document.getElementById("pdfContent").innerHTML = "<strong>Dernières lignes :</strong><br>" + lastLines;
                        }
                    });
                });
            }
        });
    };

    reader.readAsArrayBuffer(file);
});
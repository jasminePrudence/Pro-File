
// Si le message d'erreur existe, il disparaît après 5 secondes
window.onload = function() {
    var errorMessage = document.getElementById("error-message");
    if (errorMessage) {
        setTimeout(function() {
            errorMessage.style.display = "none";  // Cache le message d'erreur
        }, 3000);  // 3000 ms = 3secondes
    }
};

document.addEventListener("DOMContentLoaded", function() {
    // Sélectionner tous les inputs ayant l'ID "csv-file"
    const fileInputs = document.querySelectorAll('[id="csv-file"]');

    fileInputs.forEach(input => {
        input.addEventListener('change', function(event) {
            const file = event.target.files[0];  
            if (!file) return;

            const reader = new FileReader();

            reader.onload = function(e) {
                const binaryString = e.target.result;

                // Vérifier si jschardet est bien chargé
                if (typeof jschardet !== "undefined") {
                    const encodingInfo = jschardet.detect(binaryString);

                    // Création ou mise à jour du message
                    let resultDiv = input.nextElementSibling; 
                    if (!resultDiv || !resultDiv.classList.contains('result-message')) {
                        resultDiv = document.createElement("div");
                        resultDiv.classList.add("result-message");
                        input.parentNode.insertBefore(resultDiv, input.nextSibling);
                    }

                    if (encodingInfo.encoding) {
                        resultDiv.innerHTML = `✅ Fichier chargé avec succès ! <br> <strong>Encodage détecté :</strong> <strong>${encodingInfo.encoding}</strong> (Confiance : ${Math.round(encodingInfo.confidence * 100)}%)`;
                        resultDiv.style.color = "darkgreen";
                    } else {
                        resultDiv.innerHTML = `<p style="color: red;">❌ Impossible de détecter l'encodage.</p>`;
                    }
                } else {
                    console.error("jschardet n'est pas chargé.");
                }
            };

            reader.readAsBinaryString(file);
        });
    });
});
document.addEventListener("DOMContentLoaded", function() {
    const links = document.querySelectorAll(".link");
    let activeDiv = null; // Stocke la div actuellement surlignée

    links.forEach(link => {
        link.addEventListener("click", function(event) {
            event.preventDefault(); // Empêche le rechargement de la page
            
            const targetId = this.getAttribute("data-target"); 
            const targetDiv = document.getElementById(targetId);

            if (!targetDiv) return;

            // 🔹 Si on clique sur un autre lien, désélectionne l'ancienne div
            if (activeDiv && activeDiv !== targetDiv) {
                activeDiv.classList.remove("highlight");
            }

            // 🔹 Si la div cliquée est déjà active, on la désactive
            if (activeDiv === targetDiv) {
                targetDiv.classList.remove("highlight");
                activeDiv = null;
            } else {
                // 🔹 Sinon, on active la nouvelle div
                targetDiv.classList.add("highlight");
                activeDiv = targetDiv;
            }
        });
    });
});

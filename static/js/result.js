// fonctionnement bouton j'aime
let liked = localStorage.getItem("liked") === "true"; // Récupérer l'état
let likeCount = localStorage.getItem("likeCount") ? parseInt(localStorage.getItem("likeCount")) : 0;

const button = document.getElementById("likeBtn");
const countSpan = document.getElementById("likeCount");

// Afficher la valeur sauvegardée
countSpan.textContent = likeCount;
if (liked) button.classList.add("liked"); // Appliquer le style si déjà liké
  button.addEventListener("click", () => {
  liked = !liked; // Alterner l'état
if (liked) {
    likeCount++;
    button.classList.add("liked");
} else {
    likeCount--;
    button.classList.remove("liked");
}

countSpan.textContent = likeCount;
localStorage.setItem("likeCount", likeCount); // Sauvegarde du compteur
localStorage.setItem("liked", liked); // Sauvegarde de l'état
});

//Afficher j'aime apres le clic de téléchargement
const btn = document.getElementById("toggleLink");
const paragraph = document.getElementById("hiddenText");

// Vérifier si le paragraphe a déjà été affiché
if (localStorage.getItem("shown") === "true") {
    paragraph.style.display = "block"; // Le garder affiché
} else {
    paragraph.style.display = "none";
}

btn.addEventListener("click", () => {
    paragraph.style.display = "block"; // Afficher le paragraphe
    localStorage.setItem("shown", "true"); // Sauvegarder l'état
});

document.addEventListener("DOMContentLoaded", function() {
    var iframe = document.querySelector("iframe");
    var downloadLink = document.getElementById("toggleLink");

    // Vérifie si l'iframe est bien chargé
    iframe.addEventListener("load", function() {
        if (iframe.src && iframe.src !== "about:blank"){
            downloadLink.style.display = "none"; // Cache le lien de téléchargement
        }
    });
});

//masquer le lien de téléchargemnet s'il s'agit de la compression
document.addEventListener("DOMContentLoaded", function() {
    var link = document.getElementById("link");
    var downloadLink = document.getElementById("toggleLink");
    if (link) { // Vérifie si l'élément 'link' existe
        downloadLink.style.display = "none"; // Cache 'downloadLink'
    }
});

document.addEventListener("DOMContentLoaded", function () {
    const hiddenText = document.getElementById("hiddenText");
    const downloadLink = document.querySelector("p a[href^='/download/']");

    if (downloadLink) {
        hiddenText.style.display = "none";
    }
});

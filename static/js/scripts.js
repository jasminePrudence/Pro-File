/*!
* Start Bootstrap - Creative v7.0.7 (https://startbootstrap.com/theme/creative)
* Copyright 2013-2023 Start Bootstrap
* Licensed under MIT (https://github.com/StartBootstrap/startbootstrap-creative/blob/master/LICENSE)
*/
//
// Scripts
// 

window.addEventListener('DOMContentLoaded', event => {

    // Navbar shrink function
    var navbarShrink = function () {
        const navbarCollapsible = document.body.querySelector('#mainNav');
        if (!navbarCollapsible) {
            return;
        }
        if (window.scrollY === 0) {
            navbarCollapsible.classList.remove('navbar-shrink')
        } else {
            navbarCollapsible.classList.add('navbar-shrink')
        }

    };

    // Shrink the navbar 
    navbarShrink();

    // Shrink the navbar when page is scrolled
    document.addEventListener('scroll', navbarShrink);

    // Activate Bootstrap scrollspy on the main nav element
    const mainNav = document.body.querySelector('#mainNav');
    if (mainNav) {
        new bootstrap.ScrollSpy(document.body, {
            target: '#mainNav',
            rootMargin: '0px 0px -40%',
        });
    };

    // Collapse responsive navbar when toggler is visible
    const navbarToggler = document.body.querySelector('.navbar-toggler');
    const responsiveNavItems = [].slice.call(
        document.querySelectorAll('#navbarResponsive .nav-link')
    );
    responsiveNavItems.map(function (responsiveNavItem) {
        responsiveNavItem.addEventListener('click', () => {
            if (window.getComputedStyle(navbarToggler).display !== 'none') {
                navbarToggler.click();
            }
        });
    });

    // Activate SimpleLightbox plugin for portfolio items
    new SimpleLightbox({
        elements: '#portfolio a.portfolio-box'
    });

});

// Délai de 5 secondes (5000 ms) pour le msg succès du formulaire
setTimeout(function() {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        alert.classList.add('fade');
        setTimeout(function() {
            alert.style.display = 'none'; // Cache le message après fade
        }, 500); // Délai pour la transition de disparition
    });
}, 5000); // 5 secondes

//JS validation du numéro de téléphone
document.addEventListener("DOMContentLoaded", function () {
    const phoneInput = document.getElementById("phone");
    const phoneError = document.getElementById("phoneError");

    phoneInput.addEventListener("input", function () {
        const phonePattern = /^\+?[0-9\s\-\(\)]{7,15}$/; // Format flexible : accepte +, chiffres, espaces, tirets et parenthèses

        if (phoneInput.value.trim() === "") {
            // Si le champ est vide, on enlève les erreurs et on masque le message
            phoneInput.classList.remove("is-invalid", "is-valid");
            phoneError.style.display = "none";
        } else if (phonePattern.test(phoneInput.value)) {
            // Si le numéro est valide
            phoneInput.classList.remove("is-invalid");
            phoneInput.classList.add("is-valid");
            phoneError.style.display = "none";
        } else {
            // Si le champ est rempli mais invalide
            phoneInput.classList.remove("is-valid");
            phoneInput.classList.add("is-invalid");
            phoneError.style.display = "block";
        }
    });
});

// JavaScript pour valider l'adresse email
document.addEventListener("DOMContentLoaded", function () {
    const emailInput = document.getElementById("email");
    const emailError = document.getElementById("emailError");

    emailInput.addEventListener("input", function () {
        if (emailInput.value.trim() === "") {
            // Si le champ est vide, masquer le message d'erreur et enlever les classes Bootstrap
            emailInput.classList.remove("is-invalid", "is-valid");
            emailError.style.display = "none";
        } else if (emailInput.validity.valid) {
            // Si l'email est valide
            emailInput.classList.remove("is-invalid");
            emailInput.classList.add("is-valid");
            emailError.style.display = "none";
        } else {
            // Si l'email est renseigné mais invalide
            emailInput.classList.remove("is-valid");
            emailInput.classList.add("is-invalid");
            emailError.style.display = "block";
        }
    });
});

// JavaScript pour activer le bouton du formulaire
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("contactForm");
    const submitButton = document.getElementById("submitButton");

    function validateForm() {
        const nom = document.getElementById("nom").value.trim();
        const email = document.getElementById("email").value.trim();
        const phone = document.getElementById("phone").value.trim();
        const message = document.getElementById("message").value.trim();
        const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (nom && emailPattern.test(email) && phone && message) {
            submitButton.removeAttribute("disabled");
            submitButton.classList.remove("disabled");
        } else {
            submitButton.setAttribute("disabled", "true");
            submitButton.classList.add("disabled");
        }
    }

    form.addEventListener("input", validateForm);
});

// Modale Bootstrap du coming soon
// Sélectionner tous les boutons avec la classe 'showModalBtn'
const showModalBtns = document.querySelectorAll('.showModalBtn');
const modalElement = new bootstrap.Modal(document.getElementById('infoModal'));

// Fonction pour afficher la modale et la fermer après 5 secondes
showModalBtns.forEach(function(button) {
  button.addEventListener('click', function() {
    modalElement.show(); // Affiche la modale

    // Fermer la modale après 5 secondes
    setTimeout(function() {
      modalElement.hide(); // Cache la modale
    }, 5000); // 5000 ms = 5 secondes
  });
});

// Lancer l'affichage progressif
addRecord(0);

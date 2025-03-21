
    let likeCount = 0;
    let liked = false;

    document.getElementById("likeBtn").addEventListener("click", function() {
        liked = !liked; // Alterner l'état "liké" ou non

        if (liked) {
            likeCount++;
            this.classList.add("liked");
       // }else {
         //   likeCount--;
           // this.classList.remove("liked");
        }

        document.getElementById("likeCount").textContent = likeCount;
    });

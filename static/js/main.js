function toggleTheme() {
    document.body.classList.toggle("light");
}

function searchVideos() {
    let input = document.getElementById("searchInput").value.toLowerCase();
    let cards = document.querySelectorAll(".video-card");

    cards.forEach(card => {
        let title = card.querySelector(".video-title").innerText.toLowerCase();
        card.style.display = title.includes(input) ? "block" : "none";
    });
}

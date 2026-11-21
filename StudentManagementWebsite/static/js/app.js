document.addEventListener("DOMContentLoaded", () => {
    const menuButton = document.getElementById("menuButton");
    const sidebar = document.getElementById("sidebar");

    if (menuButton && sidebar) {
        menuButton.addEventListener("click", () => {
            sidebar.classList.toggle("sidebar-open");
        });
    }

    document.querySelectorAll(".delete-form").forEach((form) => {
        form.addEventListener("submit", (event) => {
            const message = form.dataset.confirm || "Delete this record?";
            if (!window.confirm(message)) {
                event.preventDefault();
            }
        });
    });

    document.querySelectorAll(".flash").forEach((message) => {
        window.setTimeout(() => {
            message.classList.add("flash-hidden");
        }, 4500);
    });
});

document.addEventListener("DOMContentLoaded", () => {
    const closeAllPopovers = (except = null) => {
        document.querySelectorAll("[data-notification-menu], [data-user-menu]").forEach((menu) => {
            if (menu !== except) menu.hidden = true;
        });
        document.querySelectorAll("[data-notification-toggle], [data-user-toggle]").forEach((button) => {
            if ((button.dataset.notificationToggle !== undefined && except?.dataset.notificationMenu !== undefined) ||
                (button.dataset.userToggle !== undefined && except?.dataset.userMenu !== undefined)) return;
            button.setAttribute("aria-expanded", "false");
        });
    };

    const notificationToggle = document.querySelector("[data-notification-toggle]");
    const notificationMenu = document.querySelector("[data-notification-menu]");
    if (notificationToggle && notificationMenu) {
        notificationToggle.addEventListener("click", (event) => {
            event.stopPropagation();
            const open = notificationMenu.hidden;
            closeAllPopovers(notificationMenu);
            notificationMenu.hidden = !open;
            notificationToggle.setAttribute("aria-expanded", String(open));
            const userToggle = document.querySelector("[data-user-toggle]");
            if (userToggle) userToggle.setAttribute("aria-expanded", "false");
        });
    }

    const userToggle = document.querySelector("[data-user-toggle]");
    const userMenu = document.querySelector("[data-user-menu]");
    if (userToggle && userMenu) {
        userToggle.addEventListener("click", (event) => {
            event.stopPropagation();
            const open = userMenu.hidden;
            closeAllPopovers(userMenu);
            userMenu.hidden = !open;
            userToggle.setAttribute("aria-expanded", String(open));
            const bell = document.querySelector("[data-notification-toggle]");
            if (bell) bell.setAttribute("aria-expanded", "false");
        });
    }

    document.addEventListener("click", () => closeAllPopovers());
    document.querySelectorAll("[data-notification-menu], [data-user-menu]").forEach((menu) => {
        menu.addEventListener("click", (event) => event.stopPropagation());
    });

    document.querySelectorAll("[data-dismiss-message]").forEach((button) => {
        button.addEventListener("click", () => button.closest("[data-message]")?.remove());
    });

    const mobileMenu = document.querySelector("[data-mobile-menu]");
    const sidebar = document.querySelector("[data-sidebar]");
    const backdrop = document.querySelector("[data-mobile-backdrop]");
    const toggleMobile = () => {
        sidebar?.classList.toggle("mobile-open");
        backdrop?.classList.toggle("visible");
        document.body.classList.toggle("menu-open");
    };
    mobileMenu?.addEventListener("click", toggleMobile);
    backdrop?.addEventListener("click", toggleMobile);

    const searchRoot = document.querySelector("[data-search]");
    const suggestionUrl = searchRoot?.dataset.suggestionsUrl;
    const searchInput = document.querySelector("[data-search-input]");
    const suggestionBox = document.querySelector("[data-search-suggestions]");
    let searchTimer;
    if (searchRoot && searchInput && suggestionBox) {
        const renderSuggestions = (results) => {
            suggestionBox.innerHTML = "";
            if (!results.length) {
                suggestionBox.hidden = true;
                return;
            }
            results.forEach((result) => {
                const link = document.createElement("a");
                link.href = result.url;
                link.className = "search-suggestion";
                link.innerHTML = `<span class="suggestion-type">${result.type}</span><span><strong></strong><small></small></span>`;
                link.querySelector("strong").textContent = result.title;
                link.querySelector("small").textContent = result.subtitle;
                suggestionBox.appendChild(link);
            });
            const all = document.createElement("a");
            all.href = `/crm/search/?q=${encodeURIComponent(searchInput.value.trim())}`;
            all.className = "search-all-link";
            all.textContent = "View all search results →";
            suggestionBox.appendChild(all);
            suggestionBox.hidden = false;
        };
        searchInput.addEventListener("input", () => {
            clearTimeout(searchTimer);
            const query = searchInput.value.trim();
            if (query.length < 2) {
                suggestionBox.hidden = true;
                return;
            }
            searchTimer = setTimeout(async () => {
                try {
                    const response = await fetch(`${suggestionUrl}?q=${encodeURIComponent(query)}`, {headers: {"X-Requested-With": "XMLHttpRequest"}});
                    if (!response.ok) return;
                    const data = await response.json();
                    renderSuggestions(data.results || []);
                } catch (error) {
                    suggestionBox.hidden = true;
                }
            }, 180);
        });
        searchInput.addEventListener("focus", () => {
            if (suggestionBox.children.length && searchInput.value.trim().length >= 2) suggestionBox.hidden = false;
        });
        document.addEventListener("click", (event) => {
            if (!searchRoot.contains(event.target)) suggestionBox.hidden = true;
        });
    }
});

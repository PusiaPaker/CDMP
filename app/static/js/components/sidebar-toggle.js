(function () {
    const layout = document.querySelector(".dashboard-layout");
    const sidebar = document.getElementById("app-sidebar");
    const toggle = document.getElementById("app-sidebar-toggle");
    const storageKey = "app-sidebar-collapsed";
    const mobileQuery = window.matchMedia("(max-width: 768px)");

    if (!layout || !sidebar || !toggle) {
        return;
    }

    const applyState = (collapsed) => {
        const shouldCollapse = collapsed && !mobileQuery.matches;
        layout.classList.toggle("is-sidebar-collapsed", shouldCollapse);
        toggle.setAttribute("aria-expanded", String(!shouldCollapse));
        toggle.setAttribute(
            "aria-label",
            shouldCollapse ? "Expand navigation sidebar" : "Collapse navigation sidebar"
        );
        toggle.setAttribute(
            "title",
            shouldCollapse ? "Expand navigation sidebar" : "Collapse navigation sidebar"
        );
    };

    const savedState = window.localStorage.getItem(storageKey) === "true";
    applyState(savedState);

    toggle.addEventListener("click", () => {
        const nextCollapsed = !layout.classList.contains("is-sidebar-collapsed");
        window.localStorage.setItem(storageKey, String(nextCollapsed));
        applyState(nextCollapsed);
    });

    mobileQuery.addEventListener("change", () => {
        applyState(window.localStorage.getItem(storageKey) === "true");
    });
})();

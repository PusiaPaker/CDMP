document.addEventListener("DOMContentLoaded", () => {
    const storageKey = "cdmp.sidebarCollapsed";
    const collapsedClass = "sidebar-collapsed";
    const root = document.documentElement;
    const toggle = document.querySelector("[data-sidebar-toggle]");
    const sidebar = document.getElementById("dashboard-sidebar");

    if (!toggle) {
        return;
    }

    const icon = toggle.querySelector("i");

    const syncToggleState = () => {
        const isCollapsed = root.classList.contains(collapsedClass);
        const label = isCollapsed ? "Expand sidebar" : "Collapse sidebar";
        const title = isCollapsed ? "Expand menu" : "Collapse menu";

        toggle.setAttribute("aria-expanded", String(!isCollapsed));
        toggle.setAttribute("aria-label", label);
        toggle.setAttribute("title", title);

        if (sidebar) {
            sidebar.setAttribute("aria-hidden", String(isCollapsed));

            if (isCollapsed) {
                sidebar.setAttribute("inert", "");
            } else {
                sidebar.removeAttribute("inert");
            }
        }

        if (icon) {
            icon.className = `bi ${isCollapsed ? "bi-list" : "bi-x-lg"}`;
        }
    };

    try {
        if (window.localStorage.getItem(storageKey) === "true") {
            root.classList.add(collapsedClass);
        }
    } catch (error) {
        // Ignore storage access issues and fall back to the default expanded layout.
    }

    syncToggleState();

    toggle.addEventListener("click", () => {
        root.classList.toggle(collapsedClass);

        try {
            window.localStorage.setItem(
                storageKey,
                String(root.classList.contains(collapsedClass))
            );
        } catch (error) {
            // Ignore storage access issues and keep the toggle functional for this page load.
        }

        syncToggleState();
    });
});

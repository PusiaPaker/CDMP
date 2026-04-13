(function () {
    const parser = new DOMParser();
    const scriptCache = new Map();
    const externalScriptStatus = new Map();
    const persistentStyles = [
        "/static/css/base/variables.css",
        "/static/css/base.css",
        "/static/css/layout/dashboard.css",
        "/static/css/components/sidebar.css",
        "/static/css/components/topbar.css",
        "/static/css/components/page-header.css",
        "/static/css/components/buttons.css",
        "/static/css/components/cards.css",
        "/static/css/components/footer.css",
        "/static/css/components/popup-box.css",
        "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css",
    ];
    let navigationToken = 0;

    const normalizeUrl = (value) => {
        try {
            return new URL(value, window.location.href).href;
        } catch (error) {
            return "";
        }
    };

    const excludedExternalScripts = new Set([
        normalizeUrl("/static/js/components/app-navigation.js"),
        "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js",
    ]);

    const executeScript = (code) => {
        const originalAddEventListener = document.addEventListener.bind(document);

        document.addEventListener = function (type, listener, options) {
            if (type === "DOMContentLoaded" && typeof listener === "function") {
                listener.call(document, new Event("DOMContentLoaded"));
                return;
            }

            return originalAddEventListener(type, listener, options);
        };

        try {
            Function(code)();
        } finally {
            document.addEventListener = originalAddEventListener;
        }
    };

    const isPersistentStyle = (href) => {
        return persistentStyles.some((entry) => href.includes(entry));
    };

    const syncStylesheets = async (nextDocument) => {
        const currentLinks = Array.from(document.head.querySelectorAll('link[rel="stylesheet"][href]'));
        const nextLinks = Array.from(nextDocument.head.querySelectorAll('link[rel="stylesheet"][href]'));
        const nextHrefs = new Set(nextLinks.map((link) => normalizeUrl(link.href)).filter(Boolean));

        const currentHrefs = new Set(
            Array.from(document.head.querySelectorAll('link[rel="stylesheet"][href]'))
                .map((link) => normalizeUrl(link.href))
                .filter(Boolean)
        );

        const pendingLoads = [];
        for (const link of nextLinks) {
            const href = normalizeUrl(link.href);
            if (!href || currentHrefs.has(href)) {
                continue;
            }

            const clone = link.cloneNode(true);
            const loadPromise = new Promise((resolve) => {
                clone.addEventListener("load", resolve, { once: true });
                clone.addEventListener("error", resolve, { once: true });
            });

            pendingLoads.push(loadPromise);
            document.head.appendChild(clone);
        }

        if (pendingLoads.length > 0) {
            await Promise.all(pendingLoads);
        }

        for (const link of currentLinks) {
            const href = normalizeUrl(link.href);
            if (!href || isPersistentStyle(href)) {
                continue;
            }

            if (!nextHrefs.has(href)) {
                link.remove();
            }
        }
    };

    const updatePopupOverlay = (nextDocument) => {
        document.querySelector("[data-popup-box]")?.remove();

        const nextPopup = nextDocument.querySelector("[data-popup-box]");
        const layout = document.querySelector(".dashboard-layout");

        if (nextPopup && layout) {
            layout.before(nextPopup.cloneNode(true));
        }
    };

    const replaceShell = (nextDocument) => {
        const nextLayout = nextDocument.querySelector(".dashboard-layout");
        const currentLayout = document.querySelector(".dashboard-layout");

        if (!nextLayout || !currentLayout) {
            return false;
        }

        updatePopupOverlay(nextDocument);
        currentLayout.replaceWith(nextLayout.cloneNode(true));
        document.body.className = nextDocument.body.className || "dashboard-body";
        document.title = nextDocument.title;
        return true;
    };

    const loadExternalScript = async (source) => {
        const normalized = normalizeUrl(source);
        if (!normalized || excludedExternalScripts.has(normalized)) {
            return;
        }

        const isSameOrigin = normalized.startsWith(window.location.origin);
        if (isSameOrigin) {
            if (!scriptCache.has(normalized)) {
                const response = await fetch(normalized, {
                    credentials: "same-origin",
                    headers: { "X-Requested-With": "fetch" },
                });

                if (!response.ok) {
                    throw new Error(`Failed to load script: ${normalized}`);
                }

                scriptCache.set(normalized, await response.text());
            }

            executeScript(scriptCache.get(normalized));
            return;
        }

        if (externalScriptStatus.has(normalized)) {
            await externalScriptStatus.get(normalized);
            return;
        }

        const promise = new Promise((resolve, reject) => {
            const script = document.createElement("script");
            script.src = normalized;
            script.async = false;
            script.onload = resolve;
            script.onerror = () => reject(new Error(`Failed to load script: ${normalized}`));
            document.body.appendChild(script);
        });

        externalScriptStatus.set(normalized, promise);
        await promise;
    };

    const runPageScripts = async (nextDocument) => {
        const scripts = Array.from(nextDocument.body.querySelectorAll("script"));

        for (const script of scripts) {
            if (script.type && script.type !== "text/javascript" && script.type !== "module") {
                continue;
            }

            if (script.src) {
                await loadExternalScript(script.src);
                continue;
            }

            const code = script.textContent.trim();
            if (!code) {
                continue;
            }

            executeScript(code);
        }
    };

    const isModifiedClick = (event) => {
        return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
    };

    const shouldHandleLink = (link, event) => {
        if (!link || isModifiedClick(event) || event.defaultPrevented) {
            return false;
        }

        if (link.target && link.target !== "_self") {
            return false;
        }

        if (link.hasAttribute("download") || link.dataset.noSpa === "true") {
            return false;
        }

        const url = new URL(link.href, window.location.href);
        if (url.origin !== window.location.origin) {
            return false;
        }

        if (url.hash && url.pathname === window.location.pathname && url.search === window.location.search) {
            return false;
        }

        if (url.pathname.includes("/logout")) {
            return false;
        }

        return true;
    };

    const setTransitionState = (isLoading) => {
        document.body.classList.toggle("is-page-transitioning", isLoading);
    };

    const waitForPaint = () =>
        new Promise((resolve) => {
            window.requestAnimationFrame(() => {
                window.requestAnimationFrame(resolve);
            });
        });

    const navigateTo = async (url, options = {}) => {
        const nextUrl = normalizeUrl(url);
        if (!nextUrl) {
            return;
        }

        const token = ++navigationToken;
        setTransitionState(true);

        try {
            const response = await fetch(nextUrl, {
                credentials: "same-origin",
                headers: { "X-Requested-With": "fetch" },
            });

            if (!response.ok) {
                window.location.href = nextUrl;
                return;
            }

            const html = await response.text();
            if (token !== navigationToken) {
                return;
            }

            const nextDocument = parser.parseFromString(html, "text/html");
            if (!nextDocument.querySelector(".dashboard-layout")) {
                window.location.href = nextUrl;
                return;
            }

            await syncStylesheets(nextDocument);

            const updateDom = async () => {
                if (!replaceShell(nextDocument)) {
                    window.location.href = nextUrl;
                    return;
                }

                await runPageScripts(nextDocument);
            };

            if (document.startViewTransition) {
                await document.startViewTransition(updateDom).finished;
            } else {
                await updateDom();
            }

            await waitForPaint();

            if (options.history !== "replace") {
                window.history.pushState({}, "", nextUrl);
            }

            window.scrollTo({ top: 0, left: 0, behavior: "auto" });
            document.dispatchEvent(new CustomEvent("app:navigation-complete", { detail: { url: nextUrl } }));
        } catch (error) {
            window.location.href = nextUrl;
        } finally {
            if (token === navigationToken) {
                waitForPaint().then(() => {
                    if (token === navigationToken) {
                        setTransitionState(false);
                    }
                });
            }
        }
    };

    document.addEventListener("click", (event) => {
        const link = event.target.closest("a[href]");
        if (!shouldHandleLink(link, event)) {
            return;
        }

        event.preventDefault();
        navigateTo(link.href);
    });

    window.addEventListener("popstate", () => {
        navigateTo(window.location.href, { history: "replace" });
    });
})();

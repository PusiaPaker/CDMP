(function () {
    const events = window.timelineEvents || [];
    const container = document.getElementById("globalTimelineContainer");
    const ONE_DAY_MS = 24 * 60 * 60 * 1000;

    if (!container || !Array.isArray(events)) {
        return;
    }

    if (events.length === 0) {
        container.innerHTML =
            '<div class="p-3 text-muted">This timeline does not have any dates attached to it yet.</div>';
        return;
    }

    if (!window.vis || !window.vis.DataSet || !window.vis.Timeline) {
        const listHtml = events
            .slice()
            .sort((a, b) => String(a.start).localeCompare(String(b.start)))
            .map((e) => {
                const endText = e.end ? " -> " + e.end.slice(0, 10) : "";
                return (
                    "<li><strong>" +
                    e.content +
                    "</strong> (" +
                    e.start.slice(0, 10) +
                    endText +
                    ")</li>"
                );
            })
            .join("");

        container.innerHTML =
            '<div class="p-3">' +
            '<p class="text-warning mb-2">Interactive timeline library did not load. Showing fallback list.</p>' +
            '<ul class="mb-0">' +
            listHtml +
            "</ul>" +
            "</div>";
        return;
    }

    const escapeHtml = (value) =>
        String(value ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#39;");

    const formatDateLabel = (value) => {
        if (!value) return "N/A";
        const d = new Date(value);
        if (Number.isNaN(d.getTime())) return String(value).slice(0, 10);
        return d.toLocaleDateString(undefined, {
            year: "numeric",
            month: "short",
            day: "numeric",
        });
    };

    const validEvents = events.filter((event) => !Number.isNaN(new Date(event.start).getTime()));

    if (validEvents.length === 0) {
        container.innerHTML =
            '<div class="p-3 text-muted">This timeline does not have any valid dates to display yet.</div>';
        return;
    }

    const groupMap = new Map();
    validEvents.forEach((event) => {
        if (!groupMap.has(event.project_id)) {
            groupMap.set(event.project_id, {
                id: event.project_id,
                content: event.project_title || "Untitled Project",
            });
        }
    });

    const items = new vis.DataSet(
        validEvents.map((e) => {
            const startLabel = formatDateLabel(e.start);
            const endLabel = formatDateLabel(e.end || e.start);
            const description =
                typeof e.description === "string" && e.description.trim()
                    ? e.description.trim()
                    : "No description for this event";

            const out = {
                id: e.id,
                content: e.content,
                start: e.start,
                group: e.project_id,
                title:
                    "<strong>" +
                    escapeHtml(e.content) +
                    "</strong><br>" +
                    "Project: " +
                    escapeHtml(e.project_title || "Untitled Project") +
                    "<br>" +
                    "Start: " +
                    escapeHtml(startLabel) +
                    "<br>" +
                    "End: " +
                    escapeHtml(endLabel) +
                    "<br>" +
                    "Description: " +
                    escapeHtml(description),
            };

            if (e.end) {
                out.end = e.end;
                out.className = "timeline-phase-object";
            } else {
                out.type = "box";
                out.className = "timeline-single-date-object";
            }

            return out;
        })
    );

    const groups = new vis.DataSet(
        Array.from(groupMap.values()).sort((a, b) => a.content.localeCompare(b.content))
    );

    const timeline = new vis.Timeline(container, items, groups, {
        stack: true,
        zoomKey: "ctrlKey",
        horizontalScroll: true,
        verticalScroll: true,
        height: "520px",
        maxHeight: 520,
        showCurrentTime: true,
        groupOrder: (a, b) => String(a.content).localeCompare(String(b.content)),
    });

    const startTimes = validEvents.map((event) => new Date(event.start).getTime());
    const endTimes = validEvents.map((event) => new Date(event.end || event.start).getTime());
    const minTime = Math.min(...startTimes);
    const maxTime = Math.max(...endTimes);

    timeline.setWindow(
        new Date(minTime - ONE_DAY_MS * 7),
        new Date(maxTime + ONE_DAY_MS * 7),
        { animation: false }
    );

    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const fitBtn = document.getElementById("fitBtn");

    if (zoomInBtn) zoomInBtn.addEventListener("click", () => timeline.zoomIn(0.4));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => timeline.zoomOut(0.4));
    if (fitBtn) {
        fitBtn.addEventListener("click", () => {
            timeline.setWindow(
                new Date(minTime - ONE_DAY_MS * 7),
                new Date(maxTime + ONE_DAY_MS * 7),
                { animation: false }
            );
        });
    }
})();

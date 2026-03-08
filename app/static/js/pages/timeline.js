(function () {
    const events = window.timelineEvents || [];
    const container = document.getElementById("timelineContainer");

    if (!container || !Array.isArray(events)) {
        return;
    }

    if (events.length === 0) {
        container.innerHTML =
            '<div class="p-3 text-muted">Upload a file to generate the timeline.</div>';
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

    const items = new vis.DataSet(
        events.map((e) => {
            const startLabel = formatDateLabel(e.start);
            const endLabel = formatDateLabel(e.end || e.start);
            const isMissingStart = Boolean(e.missing_start);
            const isRange = Boolean(e.end);

            const out = {
                id: e.id,
                content: e.content,
                start: e.start,
                group:
                    !isMissingStart && isRange
                        ? "dated_range"
                        : "unspecified_start",
                title:
                    "<strong>" +
                    escapeHtml(e.content) +
                    "</strong><br>" +
                    "Start: " +
                    escapeHtml(isMissingStart ? "Unspecified (inferred)" : startLabel) +
                    "<br>" +
                    "End: " +
                    escapeHtml(endLabel),
            };

            if (e.end) {
                out.end = e.end;
            } else {
                out.type = "box";
            }

            return out;
        })
    );

    const groups = new vis.DataSet([
        { id: "unspecified_start", content: "Deadlines", sortOrder: 1 },
        { id: "dated_range", content: "Timeframes", sortOrder: 2 },
    ]);

    const timeline = new vis.Timeline(container, items, groups, {
        stack: true,
        zoomKey: "ctrlKey",
        horizontalScroll: true,
        verticalScroll: true,
        height: "520px",
        maxHeight: 520,
        showCurrentTime: true,
        groupOrder: (a, b) => a.sortOrder - b.sortOrder,
    });

    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const fitBtn = document.getElementById("fitBtn");

    if (zoomInBtn) zoomInBtn.addEventListener("click", () => timeline.zoomIn(0.4));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => timeline.zoomOut(0.4));
    if (fitBtn) fitBtn.addEventListener("click", () => timeline.fit());

    timeline.fit();
})();

(function () {
    const events = window.timelineEvents || [];
    const container = document.getElementById("timelineContainer");
    const ONE_DAY_MS = 24 * 60 * 60 * 1000;
    const today = new Date();
    const rangeStart = new Date(today);
    const rangeEnd = new Date(today);
    rangeStart.setFullYear(rangeStart.getFullYear() - 1);
    rangeEnd.setFullYear(rangeEnd.getFullYear() + 5);

    if (!container || !Array.isArray(events)) {
        return;
    }

    const eventOverlapsRange = (event) => {
        const start = new Date(event.start);
        if (Number.isNaN(start.getTime())) {
            return false;
        }

        const end = event.end ? new Date(event.end) : start;
        if (Number.isNaN(end.getTime())) {
            return false;
        }

        return start <= rangeEnd && end >= rangeStart;
    };

    const filteredEvents = events.filter(eventOverlapsRange);

    if (filteredEvents.length === 0) {
        container.innerHTML =
            '<div class="timeline-empty-state">No project events fall between one year ago and five years from today.</div>';
        return;
    }

    if (!window.vis || !window.vis.DataSet || !window.vis.Timeline) {
        const listHtml = filteredEvents
            .slice()
            .sort((a, b) => String(a.start).localeCompare(String(b.start)))
            .map((e) => {
                const endText = e.end ? " -> " + String(e.end).slice(0, 10) : "";
                return (
                    "<li><strong>" +
                    e.content +
                    "</strong> (" +
                    String(e.start).slice(0, 10) +
                    endText +
                    ")</li>"
                );
            })
            .join("");

        container.innerHTML =
            '<div class="timeline-empty-state">' +
            "<p>Interactive timeline library did not load. Showing fallback list.</p>" +
            "<ul>" +
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
        filteredEvents.map((e) => {
            const startLabel = formatDateLabel(e.start);
            const endLabel = formatDateLabel(e.end || e.start);
            const isMissingStart = Boolean(e.missing_start);
            const isRange = Boolean(e.end);
            const description =
                typeof e.description === "string" && e.description.trim()
                    ? e.description.trim()
                    : "No description for this event";

            const out = {
                id: e.id,
                content: e.content,
                start: e.start,
                group: !isMissingStart && isRange ? "dated_range" : "unspecified_start",
                title:
                    "<strong>" +
                    escapeHtml(e.content) +
                    "</strong><br>" +
                    "Start: " +
                    escapeHtml(isMissingStart ? "Unspecified (inferred)" : startLabel) +
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

    const groups = new vis.DataSet([
        { id: "dated_range", content: "Phases", sortOrder: 1 },
        { id: "unspecified_start", content: "Deadlines", sortOrder: 2 },
    ]);

    const startTimes = filteredEvents.map((event) => new Date(event.start).getTime());
    const endTimes = filteredEvents.map((event) => new Date(event.end || event.start).getTime());
    const eventMinTime = Math.min(...startTimes);
    const eventMaxTime = Math.max(...endTimes);
    const fitPadding = eventMinTime === eventMaxTime
        ? ONE_DAY_MS * 7
        : Math.max(ONE_DAY_MS * 3, Math.round((eventMaxTime - eventMinTime) * 0.08));

    const fitToEvents = () => {
        timeline.setWindow(
            new Date(eventMinTime - fitPadding),
            new Date(eventMaxTime + fitPadding),
            { animation: false }
        );
    };

    const timeline = new vis.Timeline(container, items, groups, {
        stack: true,
        zoomKey: "ctrlKey",
        horizontalScroll: true,
        verticalScroll: true,
        height: "520px",
        maxHeight: 520,
        showCurrentTime: true,
        groupOrder: (a, b) => a.sortOrder - b.sortOrder,
        min: rangeStart,
        max: rangeEnd,
    });

    const zoomInBtn = document.getElementById("zoomInBtn");
    const zoomOutBtn = document.getElementById("zoomOutBtn");
    const fitBtn = document.getElementById("fitBtn");

    if (zoomInBtn) zoomInBtn.addEventListener("click", () => timeline.zoomIn(0.4));
    if (zoomOutBtn) zoomOutBtn.addEventListener("click", () => timeline.zoomOut(0.4));
    if (fitBtn) {
        fitBtn.addEventListener("click", () => {
            fitToEvents();
        });
    }

    timeline.setWindow(
        new Date(rangeStart.getTime() - ONE_DAY_MS * 7),
        new Date(rangeEnd.getTime() + ONE_DAY_MS * 7),
        { animation: false }
    );
})();

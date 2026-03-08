// this builds the actual visjs nodes and adds the properties for what it will look like
const peopleNodes = [];
const peopleEdges = [];
const nodesByLevel = new Map();
for (const personNode of peopleNodesData) {
    const nodeLevel = Number(personNode.level);

    peopleNodes.push({
        id: personNode.id,
        label: `<b>${personNode.name}</b>\n${personNode.role}\n<i>${personNode.title}</i>`,
        shape: 'box',
        margin: 20,
        font: {multi: 'html'},
        level: nodeLevel
    })

    // add who is on what level to map
    if (!nodesByLevel.has(nodeLevel)) {
        nodesByLevel.set(nodeLevel, []);
    }
    nodesByLevel.get(nodeLevel).push(personNode.id);
}

// we create arrows fom current level to level below it,
    // pointing from the lower to the upper level
const sortedLevels = Array.from(nodesByLevel.keys()).sort((a, b) => a - b);
for (let i = 0; i < sortedLevels.length - 1; i++) {
    const currentLevelIds = nodesByLevel.get(sortedLevels[i]) || [];
    const nextLevelIds = nodesByLevel.get(sortedLevels[i + 1]) || [];

    for (const fromId of currentLevelIds) {
        for (const toId of nextLevelIds) {
            peopleEdges.push({
                from: fromId,
                to: toId
            });
        }
    }
}

var nodes = new vis.DataSet(peopleNodes);
var edges = new vis.DataSet(peopleEdges);

var container = document.getElementById("organization-chart-network");
var data = {
    nodes: nodes,
    edges: edges,
};
var network = new vis.Network(container, data,{
    width: '100%',
    height: '500px',
    edges: {
        arrows: {
            from: {
                enabled: true
            }
        }
    },
    layout: {
        hierarchical: {
            enabled: true,
            direction: "UD",
            levelSeparation: 200, 
            nodeSpacing: 220, 
            treeSpacing: 260 
        }
    },
    physics: {
        hierarchicalRepulsion: {
            avoidOverlap: 1,
        }
    }
});

(() => {
        // ----------------------------------------------------
        // this part here is no longer used (it's from the old people page)
        const form = document.getElementById("xlsx-source-form");
        const rows = document.querySelectorAll(".xlsx-file-row");
        const hiddenSelectedId = document.getElementById(
            "selected-xlsx-file-id",
        );
        rows.forEach((row) => {
            row.addEventListener("click", () => {
                rows.forEach((other) => {
                    other.classList.remove("selected");
                });
                row.classList.add("selected");
                if (hiddenSelectedId) {
                    hiddenSelectedId.value = row.dataset.fileId || "";
                }
            });
        });
        // ------------------------------------------------

        const reportingMatrixChecks = document.querySelectorAll(
            ".reporting-matrix-check-button",
        );
        reportingMatrixChecks.forEach((checkbox) => {
            checkbox.addEventListener("change", async () => {
                const [personId, managerId] = checkbox.value.split(":");

                const checkedState = checkbox.checked;
                checkbox.disabled = true;

                try {
                    const response = await fetch(reportingUpdateUrl, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                            person_id: personId,
                            manager_id: managerId,
                            checked: checkedState,
                        }),
                    });

                    if (!response.ok) {
                        throw new Error("Failed to update reporting matrix");
                    }
                } catch (error) {
                    checkbox.checked = !checkedState;
                    console.error(error);
                } finally {
                    checkbox.disabled = false;
                }
            });
        });

        // the form part thing will only exist if at least one xlsx file exists
        if (form) {
            form.addEventListener("submit", (event) => {
                // TODO: add error message for when no file is selected
                // for now it just doesnt do anything other than preventing form submission
                if (!hiddenSelectedId.value) {
                    event.preventDefault();
                    return;
                }

                const submitUrl = new URL(form.action, window.location.origin);
                submitUrl.searchParams.set("file_id", hiddenSelectedId.value);
                form.action = `${submitUrl.pathname}${submitUrl.search}`;
            });
        }
    })();

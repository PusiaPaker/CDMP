(function () {
    const eventDistributionData = window.event_distribution_data || {};
    const roleDistributionData = window.role_distribution_data || {};
    const peopleNodesData = window.people_nodes_data || [];
    const reportingUpdateUrl = window.reporting_update_url;

    let orgNetwork = null;

    function buildOrgChart() {
        const orgChartContainer = document.getElementById("organization-chart-network");
        if (!orgChartContainer || peopleNodesData.length === 0) {
            return;
        }

        const nodes = peopleNodesData.map((personNode) => ({
            id: personNode.id,
            label: `<b>${personNode.name}</b>\n${personNode.role || ""}\n<i>${personNode.title || ""}</i>`,
            shape: "box",
            margin: 14,
            font: { multi: "html" },
            level: Number(personNode.level || 0),
        }));

        const edges = [];
        for (const personNode of peopleNodesData) {
            const reportsTo = personNode.reports_to || [];
            for (const managerId of reportsTo) {
                edges.push({
                    from: personNode.id,
                    to: managerId,
                    arrows: "to",
                });
            }
        }

        const data = {
            nodes: new vis.DataSet(nodes),
            edges: new vis.DataSet(edges),
        };

        const options = {
            width: "100%",
            height: "520px",
            layout: {
                hierarchical: {
                    enabled: true,
                    direction: "UD",
                    sortMethod: "directed",
                    levelSeparation: 140,
                    nodeSpacing: 180,
                    treeSpacing: 200,
                },
            },
            physics: false,
            nodes: {
                borderWidth: 1,
                shapeProperties: {
                    borderRadius: 10,
                },
            },
            edges: {
                smooth: false,
            },
        };

        if (orgNetwork) {
            orgNetwork.setData(data);
        } else {
            orgNetwork = new vis.Network(orgChartContainer, data, options);
        }
    }

    const eventCanvas = document.getElementById("event-distribution-chart");
    if (
        eventCanvas &&
        eventDistributionData.labels &&
        eventDistributionData.data &&
        eventDistributionData.data.some((value) => value > 0)
    ) {
        new Chart(eventCanvas, {
            type: "bar",
            data: {
                labels: eventDistributionData.labels,
                datasets: [
                    {
                        label: "Events",
                        data: eventDistributionData.data,
                        backgroundColor: "rgba(99, 102, 241, 0.28)",
                        borderColor: "rgba(99, 102, 241, 0.9)",
                        borderWidth: 1,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                    },
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                },
            },
        });
    }

    const roleCanvas = document.getElementById("role-distribution-chart");
    if (
        roleCanvas &&
        roleDistributionData.labels &&
        roleDistributionData.data &&
        roleDistributionData.data.some((value) => value > 0)
    ) {
        new Chart(roleCanvas, {
            type: "bar",
            data: {
                labels: roleDistributionData.labels,
                datasets: [
                    {
                        label: "People",
                        data: roleDistributionData.data,
                        backgroundColor: [
                            "#6366f1",
                            "#3b82f6",
                            "#10b981",
                            "#f59e0b",
                            "#ec4899",
                            "#8b5cf6",
                            "#0ea5e9",
                            "#22c55e",
                            "#f97316",
                            "#a855f7",
                            "#14b8a6",
                            "#eab308",
                            "#ef4444",
                            "#84cc16",
                            "#06b6d4",
                            "#f43f5e",
                            "#8b5cf6",
                            "#4f46e5",
                            "#16a34a",
                            "#fb923c"
                        ],
                        borderRadius: 6,
                        borderSkipped: false,
                    },
                ],
            },
            options: {
                indexAxis: "y",
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                        },
                    },
                    y: {
                        ticks: {
                            autoSkip: false,
                        },
                    },
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                },
            },
        });
    }

    buildOrgChart();

    const reportingMatrixChecks = document.querySelectorAll(".reporting-matrix-check-button");

    reportingMatrixChecks.forEach((checkbox) => {
        checkbox.addEventListener("change", async () => {
            const [personId, managerId] = checkbox.value.split(":");
            const checkedState = checkbox.checked;

            checkbox.disabled = true;

            try {
                const response = await fetch(reportingUpdateUrl, {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        person_id: personId,
                        manager_id: managerId,
                        checked: checkedState,
                    }),
                });

                if (!response.ok) {
                    throw new Error(`Failed to update reporting matrix: ${response.status}`);
                }

                await response.json();

                const personNode = peopleNodesData.find((node) => node.id === personId);
                if (personNode) {
                    personNode.reports_to = personNode.reports_to || [];

                    if (checkedState) {
                        if (!personNode.reports_to.includes(managerId)) {
                            personNode.reports_to.push(managerId);
                        }
                    } else {
                        personNode.reports_to = personNode.reports_to.filter(
                            (id) => id !== managerId
                        );
                    }
                }

                buildOrgChart();
            } catch (error) {
                checkbox.checked = !checkedState;
                console.error(error);
                alert("Could not update reporting matrix.");
            } finally {
                checkbox.disabled = false;
            }
        });
    });
})();

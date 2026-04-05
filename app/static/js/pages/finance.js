(function () {
    const runningTotalData = window.finance_running_total_data || {};
    const runningTotalCanvas = document.getElementById("finance-running-total-chart");

    if (
        !runningTotalCanvas ||
        !runningTotalData.labels ||
        !runningTotalData.data ||
        runningTotalData.labels.length === 0
    ) {
        return;
    }

    new Chart(runningTotalCanvas, {
        type: "line",
        data: {
            labels: runningTotalData.labels,
            datasets: [
                {
                    label: "Cumulative Spend",
                    data: runningTotalData.data,
                    borderColor: "rgba(43, 111, 22, 0.9)",
                    backgroundColor: "rgba(24, 172, 39, 0.5)",
                    fill: true,
                    tension: 0.25,
                    pointRadius: 3,
                    pointHoverRadius: 4,
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
                        callback(value) {
                            return `$${value}`;
                        },
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
})();

(function () {
    const runningTotalData = window.finance_running_total_data || {};
    const runningTotalCanvas = document.getElementById("finance-running-total-chart");
    const budgetForecastData = window.finance_budget_forecast_data || {};
    const budgetForecastCanvas = document.getElementById("finance-budget-forecast-chart");

    function currencyTick(value) {
        return `$${value}`;
    }

    function buildLineChart(canvas, labels, datasets, showLegend) {
        return new Chart(canvas, {
            type: "line",
            data: {
                labels,
                datasets,
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback(value) {
                                return currencyTick(value);
                            },
                        },
                    },
                },
                plugins: {
                    legend: {
                        display: showLegend,
                    },
                },
            },
        });
    }

    if (
        runningTotalCanvas &&
        runningTotalData.labels &&
        runningTotalData.data &&
        runningTotalData.labels.length > 0
    ) {
        buildLineChart(
            runningTotalCanvas,
            runningTotalData.labels,
            [
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
            false,
        );
    }

    if (
        budgetForecastCanvas &&
        budgetForecastData.labels &&
        budgetForecastData.actual_data &&
        budgetForecastData.forecast_data &&
        budgetForecastData.budget_data &&
        budgetForecastData.labels.length > 0
    ) {
        buildLineChart(
            budgetForecastCanvas,
            budgetForecastData.labels,
            [
                {
                    label: "Actual Spend",
                    data: budgetForecastData.actual_data,
                    borderColor: "rgba(43, 111, 22, 0.9)",
                    backgroundColor: "rgba(43, 111, 22, 0.5)",
                    fill: true,
                    tension: 0.25,
                    pointRadius: 3,
                    pointHoverRadius: 4,
                },
                {
                    label: "Projected Spend",
                    data: budgetForecastData.forecast_data,
                    borderColor: "rgba(201, 122, 16, 0.95)",
                    backgroundColor: "rgba(201, 122, 16, 0.5)",
                    fill: true,
                    tension: 0.25,
                    borderDash: [8, 6],
                    pointRadius: 3,
                    pointHoverRadius: 4,
                    spanGaps: true,
                },
                {
                    label: "Budget Limit",
                    data: budgetForecastData.budget_data,
                    borderColor: "rgba(176, 42, 55, 0.95)",
                    backgroundColor: "rgba(176, 42, 55, 0.5)",
                    fill: false,
                    borderWidth: 2,
                    pointRadius: 0,
                },
            ],
            true,
        );
    }
})();

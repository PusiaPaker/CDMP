(function () {
    const runningTotalData = window.finance_running_total_data || {};
    const runningTotalCanvas = document.getElementById("finance-running-total-chart");
    const budgetForecastData = window.finance_budget_forecast_data || {};
    const budgetForecastCanvas = document.getElementById("finance-budget-forecast-chart");
    const categorySplitData = window.finance_category_split_data || {};
    const categorySplitCanvas = document.getElementById("finance-category-split-chart");

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

    function buildCategoryBarChart(canvas, labels, data) {
        return new Chart(canvas, {
            type: "bar",
            data: {
                labels,
                datasets: [
                    {
                        label: "Spend by Category",
                        data,
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
                        maxBarThickness: 100,
                        categoryPercentage: 0.82,
                        barPercentage: 0.92,
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
                                return currencyTick(value);
                            },
                        },
                    },
                    x: {
                        ticks: {
                            autoSkip: false,
                        },
                    },
                },
                plugins: {
                    legend: {
                        display: false,
                    },
                    tooltip: {
                        callbacks: {
                            label(context) {
                                return `${context.label}: $${context.raw}`;
                            },
                        },
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
                    backgroundColor: "rgba(24, 172, 39, 0.5)",
                    fill: true,
                    tension: 0.25,
                    pointRadius: 3,
                    pointHoverRadius: 4,
                },
                {
                    label: "Projected Spend",
                    data: budgetForecastData.forecast_data,
                    borderColor: "rgba(201, 122, 16, 0.95)",
                    backgroundColor: "rgba(201, 122, 16, 0.28)",
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

    if (
        categorySplitCanvas &&
        categorySplitData.labels &&
        categorySplitData.data &&
        categorySplitData.labels.length > 0
    ) {
        buildCategoryBarChart(
            categorySplitCanvas,
            categorySplitData.labels,
            categorySplitData.data,
        );
    }
})();

/**
 * EVENT DISTRIBTUION CHART
 */
const event_distribution_data = window.event_distribution_data || {};

const ctx = document.getElementById('event-distribution-chart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: event_distribution_data.labels,
        datasets: [{
            label: '# of events',
            data: event_distribution_data.data,
            backgroundColor: 'rgba(109, 27, 241, 0.3)',
            borderColor: 'rgba(122, 100, 157, .75)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true,
        scales: {
            y: {
                beginAtZero: true,
                max: Math.ceil(Math.max(...event_distribution_data.data)*1.5)
            }
        }
    }
});

/**
 * PEOPLE ROLES DISTRIBTUION CHART
 */
const role_distribution_data = window.role_distribution_data || {}

const ctx2= document.getElementById('role-distribution-chart').getContext('2d');
const myChart2 = new Chart(ctx2, {
    type: 'doughnut',
    data: {
        labels: role_distribution_data.labels,
        datasets: [{
            data: role_distribution_data.data,
            backgroundColor: [
                "rgba(195, 122, 100, 0.75)",
                "rgba(90, 120, 160, 0.75)",   
                "rgba(110, 150, 130, 0.75)",  
                "rgba(200, 200, 125, 0.75)",  
                "rgba(160, 120, 100, 0.75)",  
                "rgba(150, 100, 120, 0.75)",  
            ],
            borderColor: 'rgba(122, 100, 157, 0.5)',
            borderWidth: 1
        }]
    },
    options: {
        responsive: true
    }
});

/**
 * DUMMY CHART 3
 */
const ctx3 = document.getElementById('dummychart3').getContext('2d');
const MyChart3 = new Chart(ctx3, {
    type: 'line',
    data: {
        labels: ['Day 1', 'Day 2', 'Day 3', 'Day 4', 'Day 5', 'Day 6', 'Day 7'],
        datasets: [{
            label: 'Issues Remaining',
            data: [7, 6, 4, 5, 3, 2, 1],
            backgroundColor: 'rgba(122, 100, 157, 0.5)',
            borderColor: 'rgba(122, 100, 157, 1)'
        }]
    }, 
    options: {
        plugins: {
            legend: {
                title: {
                    display: true,
                    text: 'Week Of: *upload date*'
                }
            }
        },
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});

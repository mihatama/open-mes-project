// ダッシュボード用JavaScript
document.addEventListener('DOMContentLoaded', function() {
    const ctx = document.getElementById('productionChart').getContext('2d');
    const chart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '生産数',
                data: [],
                borderColor: '#4e73df',
                backgroundColor: 'rgba(78, 115, 223, 0.05)',
                tension: 0.4
            }]
        },
        options: chartConfig
    });

    // リアルタイムデータ更新
    const eventSource = new EventSource('/dashboard/stream/');
    
    eventSource.onmessage = function(e) {
        const data = JSON.parse(e.data);
        updateChart(chart, data);
        updateLogTable(data);
    };

    function updateChart(chart, data) {
        if(chart.data.labels.length >= 15) {
            chart.data.labels.shift();
            chart.data.datasets[0].data.shift();
        }
        chart.data.labels.push(new Date().toLocaleTimeString());
        chart.data.datasets[0].data.push(data.value);
        chart.update();
    }

    function updateLogTable(data) {
        const logEntry = document.createElement('tr');
        logEntry.innerHTML = `
            <td>${new Date().toLocaleTimeString()}</td>
            <td>${data.instruction}</td>
            <td class="status-${data.status}">${data.status}</td>
        `;
        document.getElementById('logEntries').prepend(logEntry);
    }
});

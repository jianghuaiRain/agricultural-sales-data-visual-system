async function loadRegionBar() {
  const limit = 10;
  const res = await fetch(`/api/region-sales?limit=${limit}`);
  const data = await res.json();
  const labels = data.map(d => d.name);   // 品类大类
  const values = data.map(d => d.value);  // 该大类销量最高城市的销量
  const cities = data.map(d => d.city);   // 该大类销量最高的城市
  const ctx = document.getElementById('regionBarChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'horizontalBar',
    data: {
      labels,
      datasets: [{
        label: '销量（斤）',
        data: values,
        backgroundColor: 'rgba(28, 200, 138, 0.5)',
        borderColor: 'rgba(28, 200, 138, 1)',
        borderWidth: 1,
        cities
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        xAxes: [{
          ticks: {
            beginAtZero: true,
            callback: function(value) { return value + '斤'; }
          }
        }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, chart) {
            const ds = chart.datasets[tooltipItem.datasetIndex];
            const city = ds.cities ? ds.cities[tooltipItem.index] : '';
            return `最多城市：${city}，销量：${tooltipItem.xLabel}斤`;
          }
        }
      }
    }
  });
}
document.addEventListener('DOMContentLoaded', loadRegionBar);

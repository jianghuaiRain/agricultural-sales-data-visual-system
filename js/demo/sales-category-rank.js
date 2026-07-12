async function loadSalesCategoryRank() {
  const year = 2025;
  const limit = 15;
  const res = await fetch(`/api/top-subcategories?year=${year}&limit=${limit}`);
  const data = await res.json();
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('salesCategoryRankChart');
  if (!ctx || !window.Chart) return;
  if (ctx.getAttribute('data-initialized') === 'true') return;
  ctx.setAttribute('data-initialized', 'true');
  new Chart(ctx, {
    type: 'horizontalBar',
    data: {
      labels,
      datasets: [{
        label: '销量',
        data: values,
        backgroundColor: 'rgba(54, 185, 204, 0.6)',
        borderColor: 'rgba(54, 185, 204, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        xAxes: [{
          ticks: {
            beginAtZero: true
          }
        }],
        yAxes: [{
          barPercentage: 0.7
        }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, chart) {
            const name = chart.labels[tooltipItem.index] || '';
            const unit = /种子|种苗/.test(name) ? '棵' : '斤';
            return '销量：' + tooltipItem.xLabel + unit;
          }
        }
      }
    }
  });
}
window.loadSalesCategoryRank = loadSalesCategoryRank;

async function loadCategoryPie() {
  const res = await fetch('/api/category-share');
  const data = await res.json();
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const total = values.reduce((a, b) => a + b, 0) || 1;
  const ctx = document.getElementById('categoryPieChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        label: '销量（斤）',
        data: values,
        backgroundColor: [
          '#4e73df','#1cc88a','#36b9cc','#f6c23e','#e74a3b',
          '#858796','#5a5c69','#20c997','#6610f2','#fd7e14'
        ]
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, chartData) {
            const idx = tooltipItem.index;
            const name = chartData.labels[idx];
            const val = chartData.datasets[0].data[idx] || 0;
            const pct = Math.round(val / total * 10000) / 100;
            const unit = /种子|种苗/.test(name) ? '棵' : '斤';
            return `${name}: ${val}${unit} (${pct}%)`;
          }
        }
      }
    }
  });
}
document.addEventListener('DOMContentLoaded', loadCategoryPie);

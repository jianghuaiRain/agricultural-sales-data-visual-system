async function loadProductsBar() {
  const res = await fetch('/api/top-categories?limit=10');
  const data = await res.json();
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('productsBarChart');
  if (!ctx) return;
  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '成交量',
        data: values,
        backgroundColor: 'rgba(78, 115, 223, 0.5)',
        borderColor: 'rgba(78, 115, 223, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        yAxes: [{ 
          ticks: { beginAtZero: true,
            callback: function(value, index) { 
              return value; 
            } 
          } 
        }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, chart) {
            const name = chart.labels[tooltipItem.index] || '';
            const unit = /种子|种苗/.test(name) ? '棵' : '斤';
            return '成交量：' + tooltipItem.yLabel + unit;
          }
        }
      }
    }
  });
}
document.addEventListener('DOMContentLoaded', loadProductsBar);

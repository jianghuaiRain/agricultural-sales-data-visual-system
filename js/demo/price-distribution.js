function initPriceDistribution() {
  const metricSel = document.getElementById('priceDistMetric');
  function reload() {
    const metric = metricSel.value || 'count';
    loadPriceDistribution(metric);
  }
  if (!metricSel.getAttribute('data-bind')) {
    metricSel.addEventListener('change', reload);
    metricSel.setAttribute('data-bind', 'true');
  }
  reload();
}

let priceDistChartInstance = null;
async function loadPriceDistribution(metric) {
  const res = await fetch(`/api/price-distribution?metric=${metric}&bins=20`);
  const data = await res.json();
  const labels = data.map(d => d.bin);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('priceDistChart');
  if (!ctx || !window.Chart) return;
  if (priceDistChartInstance) {
    try { priceDistChartInstance.destroy(); } catch(e) {}
    priceDistChartInstance = null;
  }
  priceDistChartInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: metric === 'sales' ? '销量（斤）' : '数量（条）',
        data: values,
        backgroundColor: 'rgba(28, 200, 138, 0.5)',
        borderColor: 'rgba(28, 200, 138, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        xAxes: [{ gridLines: { display: false }, ticks: { maxRotation: 0, minRotation: 0, autoSkip: true } }],
        yAxes: [{ ticks: { beginAtZero: true } }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem) {
            const unit = metric === 'sales' ? '斤' : '条';
            return '值：' + tooltipItem.yLabel + unit;
          }
        }
      }
    }
  });
}
window.initPriceDistribution = initPriceDistribution;

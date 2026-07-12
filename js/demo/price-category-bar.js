function initPriceCategoryBar() {
  const levelSel = document.getElementById('priceAvgLevel');
  function reload() {
    const level = levelSel.value || 'category';
    loadPriceCategoryBar(level);
  }
  if (!levelSel.getAttribute('data-bind')) {
    levelSel.addEventListener('change', reload);
    levelSel.setAttribute('data-bind', 'true');
  }
  reload();
}

let priceCategoryBarInstance = null;
async function loadPriceCategoryBar(level) {
  const res = await fetch(`/api/category-avg-price?level=${level}`);
  const data = await res.json();
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('priceCategoryBarChart');
  if (!ctx || !window.Chart) return;
  if (priceCategoryBarInstance) {
    try { priceCategoryBarInstance.destroy(); } catch(e) {}
    priceCategoryBarInstance = null;
  }
  priceCategoryBarInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '平均价（元）',
        data: values,
        backgroundColor: 'rgba(231, 74, 59, 0.5)',
        borderColor: 'rgba(231, 74, 59, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        yAxes: [{ ticks: { beginAtZero: true } }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem) {
            return '平均价：' + tooltipItem.yLabel + '元';
          }
        }
      }
    }
  });
}
window.initPriceCategoryBar = initPriceCategoryBar;

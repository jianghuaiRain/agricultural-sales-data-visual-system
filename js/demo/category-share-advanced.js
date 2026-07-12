function initCategoryShareAdvanced() {
  const metricSel = document.getElementById('categoryShareMetric');
  const levelSel = document.getElementById('categoryShareLevel');
  const typeSel = document.getElementById('categoryShareType');
  function reload() {
    const metric = metricSel.value;
    const level = levelSel.value;
    const type = typeSel.value;
    loadCategoryShareAdvanced(metric, level, type);
  }
  if (!metricSel.getAttribute('data-bind')) {
    metricSel.addEventListener('change', reload);
    levelSel.addEventListener('change', reload);
    typeSel.addEventListener('change', reload);
    metricSel.setAttribute('data-bind', 'true');
  }
  reload();
}

let categoryShareChartInstance = null;
async function loadCategoryShareAdvanced(metric, level, type) {
  const res = await fetch(`/api/category-share-advanced?metric=${metric}&level=${level}`);
  const data = await res.json();
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('categoryShareChart');
  if (!ctx || !window.Chart) return;
  if (categoryShareChartInstance) {
    try { categoryShareChartInstance.destroy(); } catch(e) {}
    categoryShareChartInstance = null;
  }
  const baseDataset = {
    data: values,
    backgroundColor: labels.map((_, i) => ['#4e73df','#1cc88a','#36b9cc','#f6c23e','#e74a3b','#858796','#5a5c69','#20c997','#6610f2','#fd7e14'][i % 10])
  };
  const chartConfig = {
    type: type === 'pie' ? 'pie' : (type === 'bar' ? 'bar' : 'doughnut'),
    data: {
      labels,
      datasets: [baseDataset]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      legend: { position: 'bottom' },
      scales: type === 'bar' ? { 
        xAxes: [{ stacked: true }], 
        yAxes: [{ stacked: true, ticks: { beginAtZero: true } }] 
      } : undefined,
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            const idx = tooltipItem.index;
            const name = labels[idx];
            const val = values[idx];
            const sum = values.reduce((a,b)=>a+b,0) || 1;
            const pct = (val / sum * 100).toFixed(2);
            const unit = metric === 'amount' ? '元' : (/种子|种苗/.test(name) ? '棵' : '斤');
            if (type === 'bar') return `${name}：${val}${unit}`;
            return `${name}：${val}${unit}（${pct}%）`;
          }
        }
      }
    }
  };
  categoryShareChartInstance = new Chart(ctx, chartConfig);
}
window.initCategoryShareAdvanced = initCategoryShareAdvanced;

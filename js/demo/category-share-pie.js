async function loadCategorySharePie() {
  const res = await fetch('/api/category-share-pie');
  let data = [];
  try {
    data = await res.json();
  } catch (e) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '加载失败';
    return;
  }
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('categorySharePieChart');
  if (!ctx || !window.Chart) return;
  if (!data || data.length === 0) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '暂无数据';
    return;
  }
  if (window.__categorySharePieChart__) {
    try { window.__categorySharePieChart__.destroy(); } catch(e) {}
    window.__categorySharePieChart__ = null;
  }
  window.__categorySharePieChart__ = new Chart(ctx, {
    type: 'pie',
    data: {
      labels,
      datasets: [{
        data: values,
        backgroundColor: labels.map((_, i) => ['#4e73df','#1cc88a','#36b9cc','#f6c23e','#e74a3b','#858796','#5a5c69','#20c997','#6610f2','#fd7e14'][i % 10])
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            const idx = tooltipItem.index;
            const name = labels[idx];
            const val = values[idx];
            const sum = values.reduce((a,b)=>a+b,0) || 1;
            const pct = (val / sum * 100).toFixed(2);
            const unit = /种子|种苗/.test(name) ? '棵' : '斤';
            return `${name}：${val}${unit}（${pct}%）`;
          }
        }
      },
      legend: { position: 'bottom' }
    }
  });
}
window.loadCategorySharePie = loadCategorySharePie;

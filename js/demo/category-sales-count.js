async function loadCategorySalesCount() {
  const res = await fetch('/api/category-sales-count');
  let data = [];
  try {
    data = await res.json();
  } catch (e) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '加载失败';
    return;
  }
  const labels = data.map(d => d.name);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('categorySalesCountChart');
  if (!ctx || !window.Chart) return;
  if (!data || data.length === 0) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '暂无数据';
    return;
  }
  if (window.__categorySalesCountChart__) {
    try { window.__categorySalesCountChart__.destroy(); } catch(e) {}
    window.__categorySalesCountChart__ = null;
  }
  window.__categorySalesCountChart__ = new Chart(ctx, {
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
      scales: { yAxes: [{ ticks: { beginAtZero: true } }] },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, data) {
            const name = data.labels[tooltipItem.index] || '';
            const unit = /种子|种苗/.test(name) ? '棵' : '斤';
            return '成交量：' + tooltipItem.yLabel + unit;
          }
        }
      }
    }
  });
  window.addEventListener('resize', function(){ 
    if (window.__categorySalesCountChart__) window.__categorySalesCountChart__.resize(); 
  });
}
window.loadCategorySalesCount = loadCategorySalesCount;

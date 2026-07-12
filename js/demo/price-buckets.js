async function loadPriceBuckets() {
  const res = await fetch('/api/price-buckets');
  let data = [];
  try {
    data = await res.json();
  } catch (e) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '加载失败';
    return;
  }
  const labels = data.map(d => d.bin);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('priceBucketChart');
  if (!ctx || !window.Chart) return;
  if (!data || data.length === 0) {
    if (ctx && ctx.parentElement) ctx.parentElement.innerHTML = '暂无数据';
    return;
  }
  if (window.__priceBucketChart__) {
    try { window.__priceBucketChart__.destroy(); } catch(e) {}
    window.__priceBucketChart__ = null;
  }
  window.__priceBucketChart__ = new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [{
        label: '商品数',
        data: values,
        backgroundColor: 'rgba(40, 167, 69, 0.5)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 1
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        xAxes: [{ gridLines: { display: false }, ticks: { maxRotation: 0, minRotation: 0 } }],
        yAxes: [{ ticks: { beginAtZero: true } }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem) { return '商品数：' + tooltipItem.yLabel; }
        }
      }
    }
  });
  window.addEventListener('resize', function(){
    if (window.__priceBucketChart__) window.__priceBucketChart__.resize();
  });
}
window.loadPriceBuckets = loadPriceBuckets;

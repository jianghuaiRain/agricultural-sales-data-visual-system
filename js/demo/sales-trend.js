function initSalesTrend() {
  const select = document.getElementById('trendGranularity');
  if (!select) return;
  function reload() {
    const freq = select.value || 'day';
    loadSalesTrend(freq);
  }
  if (!select.getAttribute('data-bind')) {
    select.addEventListener('change', reload);
    select.setAttribute('data-bind', 'true');
  }
  reload();
}

let salesTrendChartInstance = null;
async function loadSalesTrend(freq) {
  const year = 2025;
  const res = await fetch(`/api/sales-trend?year=${year}&freq=${freq}`);
  const data = await res.json();
  const labels = data.map(d => d.label || d.date);
  const values = data.map(d => d.value);
  const ctx = document.getElementById('salesTrendChart');
  if (!ctx || !window.Chart) return;
  if (salesTrendChartInstance) {
    try { salesTrendChartInstance.destroy(); } catch(e) {}
    salesTrendChartInstance = null;
  }
  salesTrendChartInstance = new Chart(ctx, {
    type: 'line',
    data: {
      labels,
      datasets: [{
        label: '销量',
        data: values,
        backgroundColor: 'rgba(78, 115, 223, 0.2)',
        borderColor: 'rgba(78, 115, 223, 1)',
        borderWidth: 2,
        pointRadius: 1.5,
        fill: true
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        xAxes: [{
          gridLines: { display: false },
          ticks: {
            autoSkip: true,
            maxTicksLimit: (freq === 'day' ? 15 : (freq === 'week' ? 12 : 12)),
            callback: function(value) {
              var v = value || '';
              var m = v.match(/^(\d{4})-(\d{2})-(\d{2})$/);
              if (m) return m[1] + '-' + m[2] + '-' + m[3];
              var m2 = v.match(/^(\d{4})-(\d{2})$/);
              if (m2) return v;
              var d = new Date(v);
              if (!isNaN(d.getTime())) {
                var y = d.getFullYear();
                var mm = ('0' + (d.getMonth() + 1)).slice(-2);
                var dd = ('0' + d.getDate()).slice(-2);
                return y + '-' + mm + '-' + dd;
              }
              return v;
            }
          }
        }],
        yAxes: [{
          ticks: { beginAtZero: true }
        }]
      },
      legend: { display: false },
      tooltips: {
        callbacks: {
          label: function(tooltipItem, chart) {
            const unit = '斤';
            return '销量：' + tooltipItem.yLabel + unit;
          }
        }
      }
    }
  });
}
window.initSalesTrend = initSalesTrend;

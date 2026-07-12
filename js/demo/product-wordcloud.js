async function loadProductWordCloud() {
  const el = document.getElementById('productWordCloud');
  if (!el || typeof echarts === 'undefined') return;
  const res = await fetch('/api/product-wordcloud');
  let data = [];
  try { data = await res.json(); } catch (e) { data = []; }
  if (!Array.isArray(data) || data.length === 0) {
    el.innerHTML = '<div style="text-align:center;color:#858796;padding:40px;">暂无词云数据</div>';
    return;
  }
  data = data.filter(d => d && d.name && d.value > 0).sort((a,b)=>b.value-a.value).slice(0, 100);
  const chart = echarts.init(el);
  chart.setOption({
    tooltip: {
      formatter: function (item) {
        return item.name + '<br/>出现次数：' + item.value;
      }
    },
    series: [{
      type: 'wordCloud',
      shape: 'square',
      gridSize: 8,
      sizeRange: [12, 46],
      rotationRange: [0, 0],
      textStyle: {
        color: function () {
          const colors = ['#4e73df','#1cc88a','#36b9cc','#f6c23e','#e74a3b','#858796','#5a5c69','#20c997','#6610f2','#fd7e14'];
          return colors[Math.floor(Math.random() * colors.length)];
        }
      },
      emphasis: { focus: 'self' },
      data: data
    }]
  });
  let t = null;
  window.addEventListener('resize', function() {
    if (t) clearTimeout(t);
    t = setTimeout(function(){ chart.resize(); }, 150);
  });
}
document.addEventListener('DOMContentLoaded', loadProductWordCloud);

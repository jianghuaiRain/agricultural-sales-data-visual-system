let regionMapInstance = null
async function loadRegionMap(metric) {
  const el = document.getElementById('regionMapChart');
  if (!el || typeof echarts === 'undefined') return;
  metric = metric || (document.getElementById('regionMapMetric')?.value || 'sales');
  // 加载数据
  const res = await fetch(`/api/region-map?level=province&metric=${metric}`);
  let data = [];
  try { data = await res.json(); } catch(e) { data = []; }
  // 加载中国地图 GeoJSON（省级）
  let geojson = null;
  try {
    const r = await fetch('https://geo.datav.aliyun.com/areas_v3/bound/geojson?code=100000_full');
    geojson = await r.json();
  } catch(e) {}
  if (!geojson) {
    el.innerHTML = '<div style="text-align:center;color:#858796;padding:40px;">地图数据加载失败</div>';
    return;
  }
  echarts.registerMap('china', geojson);
  if (regionMapInstance) {
    try { regionMapInstance.dispose(); } catch(e) {}
    regionMapInstance = null;
  }
  regionMapInstance = echarts.init(el);
  const maxVal = Math.max.apply(null, data.map(d=>d.value)) || 1;
  regionMapInstance.setOption({
    tooltip: {
      formatter: function(params){
        const name = params.name || '';
        const val = params.value || 0;
        if (metric === 'topcat') {
          const cat = (params.data && params.data.cat) ? params.data.cat : '未知品类';
          return `${name}<br/>主要品类：${cat}`;
        }
        const unit = metric === 'amount' ? '元' : '斤';
        return `${name}<br/>${metric==='amount'?'销售额':'销量'}：${val}${unit}`;
      }
    },
    visualMap: {
      min: 0,
      max: maxVal,
      left: 'left',
      bottom: 0,
      text: ['高','低'],
      inRange: { color: ['#e0f3f8', '#99d8c9', '#2ca25f'] },
      calculable: true
    },
    series: [{
      type: 'map',
      map: 'china',
      roam: true,
      label: { show: false },
      data: data
    }]
  });
  let t = null;
  window.addEventListener('resize', function(){
    if (t) clearTimeout(t);
    t = setTimeout(function(){ regionMapInstance && regionMapInstance.resize(); }, 100);
  });
}

function initRegionMap() {
  const metricSel = document.getElementById('regionMapMetric');
  if (metricSel && !metricSel.getAttribute('data-bind')) {
    metricSel.addEventListener('change', function(){ loadRegionMap(metricSel.value); });
    metricSel.setAttribute('data-bind','true');
  }
  loadRegionMap(metricSel?.value || 'sales');
}
window.initRegionMap = initRegionMap

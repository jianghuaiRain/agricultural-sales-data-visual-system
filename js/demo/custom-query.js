let cqChart = null;
async function initCustomQuery() {
  await cqLoadOptions();
  document.getElementById('cqApply').addEventListener('click', cqApply);

  // 省份联动城市
  const provEl = document.getElementById('cqProvince');
  if (provEl) {
    provEl.addEventListener('change', async () => {
      const province = provEl.value;
      const res = await fetch(`/api/cities-by-province?province=${encodeURIComponent(province)}`);
      let cities = [];
      try { cities = await res.json(); } catch(e) { cities = []; }
      const cityEl = document.getElementById('cqCity');
      if (cityEl) {
        cityEl.innerHTML = '';
        cityEl.appendChild(new Option('全部', ''));
        cities.forEach(v => cityEl.appendChild(new Option(v, v)));
      }
    });
  }

  // 默认时间范围：2025年整年
  const startEl = document.getElementById('cqStart');
  const endEl = document.getElementById('cqEnd');
  if (startEl && !startEl.value) startEl.value = '2025-01-01';
  if (endEl && !endEl.value) endEl.value = '2025-12-31';
  // 限制可选范围
  if (startEl) { startEl.min = '2025-01-01'; startEl.max = '2025-12-31'; }
  if (endEl) { endEl.min = '2025-01-01'; endEl.max = '2025-12-31'; }
  // 默认一次
  cqApply();
}

async function cqLoadOptions() {
  const res = await fetch('/api/custom-query-options');
  let opts = {};
  try { opts = await res.json(); } catch(e) { opts = {}; }
  const fill = (id, list, withEmpty=true) => {
    const el = document.getElementById(id);
    if (!el) return;
    el.innerHTML = '';
    if (withEmpty) el.appendChild(new Option('全部',''));
    (list || []).forEach(v => el.appendChild(new Option(v, v)));
  };
  fill('cqCategory', opts.categories);
  fill('cqSubcategory', opts.subcategories);
  fill('cqProvince', opts.provinces);
  fill('cqCity', opts.cities);
  fill('cqProduct', opts.products);
}

async function cqApply() {
  const dim = document.getElementById('cqDimension').value;
  const metric = document.getElementById('cqMetric').value;
  const chartType = document.getElementById('cqChartType').value;
  const params = new URLSearchParams({
    dimension: dim,
    metric: metric,
    gran: 'month',
    start: clampDate(document.getElementById('cqStart').value || '2025-01-01'),
    end: clampDate(document.getElementById('cqEnd').value || '2025-12-31'),
    category: document.getElementById('cqCategory').value || '',
    subcategory: document.getElementById('cqSubcategory').value || '',
    province: document.getElementById('cqProvince').value || '',
    city: document.getElementById('cqCity').value || '',
    product: document.getElementById('cqProduct').value || '',
    pmin: document.getElementById('cqPmin').value || '',
    pmax: document.getElementById('cqPmax').value || '',
    limit: '20'
  });
  const res = await fetch('/api/custom-query-data?' + params.toString());
  let data = [];
  try { data = await res.json(); } catch(e) { data = []; }
  // 空数据提示
  if (!Array.isArray(data) || data.length === 0) {
    const elChart = document.getElementById('customQueryChart');
    const elTable = document.getElementById('customQueryTable');
    if (cqChart) { try { cqChart.dispose(); } catch(e){} cqChart = null; }
    if (elTable) elTable.style.display = 'none';
    if (elChart) {
      elChart.style.display = '';
      elChart.innerHTML = '<div style="height:420px;display:flex;align-items:center;justify-content:center;color:#858796;">暂无数据</div>';
    }
    return;
  }
  cqRender(chartType, dim, metric, data);
}

function clampDate(val) {
  try {
    const min = new Date('2025-01-01');
    const max = new Date('2025-12-31');
    const d = new Date(val);
    if (isNaN(d.getTime())) return '2025-01-01';
    if (d < min) return '2025-01-01';
    if (d > max) return '2025-12-31';
    // 格式化为 YYYY-MM-DD
    const y = d.getFullYear();
    const m = ('0' + (d.getMonth()+1)).slice(-2);
    const da = ('0' + d.getDate()).slice(-2);
    return `${y}-${m}-${da}`;
  } catch (e) {
    return '2025-01-01';
  }
}

function cqRender(chartType, dim, metric, data) {
  const elChart = document.getElementById('customQueryChart');
  const elTable = document.getElementById('customQueryTable');
  const head = document.getElementById('cqTableHead');
  const body = document.getElementById('cqTableBody');
  if (!elChart || typeof echarts === 'undefined') return;
  // 表格渲染
  if (chartType === 'table') {
    elChart.style.display = 'none';
    elTable.style.display = '';
    head.innerHTML = '<th>名称/时间</th><th>' + (metric==='amount'?'销售额':'销量') + '</th>';
    if (!Array.isArray(data) || data.length === 0) {
      body.innerHTML = '<tr><td colspan="2" class="text-center">无</td></tr>';
    } else {
      body.innerHTML = (data || []).map(d => `<tr><td>${d.label || d.date || ''}</td><td>${d.value || 0}</td></tr>`).join('');
    }
    return;
  }
  elTable.style.display = 'none';
  elChart.style.display = '';
  elChart.innerHTML = ''; // 清空“暂无数据”占位
  if (cqChart) { try { cqChart.dispose(); } catch(e){} cqChart = null; }
  cqChart = echarts.init(elChart);
  const labels = (data || []).map(d => d.label || d.date);
  const values = (data || []).map(d => d.value || 0);
  let series;
  if (chartType === 'pie') {
    series = [{ type: 'pie', radius: '65%', data: labels.map((l,i)=>({name:l, value:values[i]})) }];
  } else {
    series = [{ type: chartType === 'line' ? 'line' : 'bar', data: values, smooth: chartType==='line' }];
  }
  cqChart.setOption({
    tooltip: { trigger: chartType==='pie' ? 'item' : 'axis' },
    xAxis: chartType==='pie' ? undefined : { type: 'category', data: labels, axisLabel: { interval: 0, rotate: 0 } },
    yAxis: chartType==='pie' ? undefined : { type: 'value' },
    series: series,
    legend: chartType==='pie' ? {} : undefined
  });
  let t = null;
  window.addEventListener('resize', function(){
    if (t) clearTimeout(t);
    t = setTimeout(function(){ cqChart && cqChart.resize(); }, 100);
  });
}

window.initCustomQuery = initCustomQuery;

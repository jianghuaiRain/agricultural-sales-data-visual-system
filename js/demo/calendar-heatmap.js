async function loadCalendarHeatmap() {
  const year = 2025;
  const res = await fetch('/api/daily-heatmap?year=' + year);
  const data = await res.json();
  const el = document.getElementById('salesCalendarHeatmap');
  if (!el || typeof echarts === 'undefined') return;
  const chart = echarts.init(el);
  const items = data.map(d => ({ date: d.date, value: Number(d.value) || 0 }));
  function inRange(dt, start, end) {
    const t = new Date(dt);
    return t >= new Date(start) && t <= new Date(end);
  }
  const ranges = [
    [`${year}-01-01`, `${year}-03-31`],
    [`${year}-04-01`, `${year}-06-30`],
    [`${year}-07-01`, `${year}-09-30`],
    [`${year}-10-01`, `${year}-12-31`]
  ];
  const quarters = ranges.map(([s, e]) =>
    items.filter(x => inRange(x.date, s, e)).map(x => [x.date, x.value])
  );
  const qMax = quarters.map(q => q.reduce((m, x) => Math.max(m, x[1] || 0), 0) || 1);
  const colors = ['#313695','#4575b4','#74add1','#abd9e9','#e0f3f8','#ffffbf','#fee090','#fdae61','#f46d43','#d73027','#a50026'];
  const globalMax = Math.max.apply(null, qMax);
  chart.setOption({
    tooltip: {
      formatter: function (params) {
        const date = params.data[0];
        const val = params.data[1] || 0;
        return `${date}<br/>销量：${val}斤`;
      }
    },
    visualMap: {
      min: 0,
      max: globalMax,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 20,
      inRange: { color: colors },
      seriesIndex: [0, 1, 2, 3]
    },
    calendar: [
      { range: ranges[0], top: 10, left: '5%', right: '5%', cellSize: [18, 18], splitLine: { show: true }, itemStyle: { borderWidth: 0.5 } },
      { range: ranges[1], top: 150, left: '5%', right: '5%', cellSize: [18, 18], splitLine: { show: true }, itemStyle: { borderWidth: 0.5 } },
      { range: ranges[2], top: 290, left: '5%', right: '5%', cellSize: [18, 18], splitLine: { show: true }, itemStyle: { borderWidth: 0.5 } },
      { range: ranges[3], top: 430, left: '5%', right: '5%', cellSize: [18, 18], splitLine: { show: true }, itemStyle: { borderWidth: 0.5 } }
    ],
    series: [
      { type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: 0, data: quarters[0] },
      { type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: 1, data: quarters[1] },
      { type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: 2, data: quarters[2] },
      { type: 'heatmap', coordinateSystem: 'calendar', calendarIndex: 3, data: quarters[3] }
    ]
  });
  window.addEventListener('resize', function(){ chart.resize(); });
}
window.loadCalendarHeatmap = loadCalendarHeatmap;

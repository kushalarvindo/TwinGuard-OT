const http = require('http');

http.get('http://127.0.0.1:8000/api/analytics/anomaly', (res) => {
  let body = '';
  res.on('data', chunk => body += chunk);
  res.on('end', () => {
    const data = JSON.parse(body);
    const timeseries = data.timeseries || [];
    const detections = data.detections || [];
    
    function fmtTime(ts) {
      return new Date(ts * 1000).toLocaleTimeString(undefined, { hour12: false });
    }

    const chartData = timeseries.slice(-5).map(r => ({
      t: fmtTime(Number(r.timestamp)),
      true_level: Number(r.true_level),
      sensor_level: Number(r.sensor_level),
      residual: Number(r.process_residual),
      label: Number(r.label),
      attack: r.attack_type !== 'normal' ? Number(r.true_level) : null,
      RAW: r
    }));
    
    const detChartData = detections.slice(-5).map(r => ({
      t: fmtTime(Number(r.timestamp)),
      score: Number(r.anomaly_score),
      is_anomaly: Number(r.is_anomaly),
      RAW: r
    }));

    console.log("CHART DATA:\n", JSON.stringify(chartData, null, 2));
    console.log("DET CHART DATA:\n", JSON.stringify(detChartData, null, 2));
  });
});

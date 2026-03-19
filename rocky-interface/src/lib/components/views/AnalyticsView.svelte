<script context="module" lang="ts">
  export type AnalyticsWidget = {
    title: string;
    html: string;
  };

  // Widget data synced with right-side widget bar when Analytics frame is active
  export const analyticsWidgets: AnalyticsWidget[] = [
    {
      title: 'Temperature Trend',
      html: `
        <div class="widget-metric">71°F</div>
        <p class="widget-note">Campus server room average</p>
        <div class="mini-bars" aria-label="Temperature trend bars">
          <span style="--h:40%"></span>
          <span style="--h:52%"></span>
          <span style="--h:58%"></span>
          <span style="--h:64%"></span>
          <span style="--h:61%"></span>
          <span style="--h:68%"></span>
        </div>
      `
    },
    {
      title: 'Request Mix',
      html: `
        <div class="widget-metric">1,284</div>
        <p class="widget-note">Model requests in the last 24h</p>
        <div class="mini-pie" role="img" aria-label="68 percent successful, 20 percent queued, 12 percent flagged"></div>
      `
    },
    {
      title: 'Flagged Queue',
      html: `
        <div class="widget-metric">12</div>
        <p class="widget-note">Open items awaiting review</p>
        <div class="widget-stat-grid">
          <div><strong>5</strong><span>Safety</span></div>
          <div><strong>4</strong><span>Policy</span></div>
          <div><strong>3</strong><span>Other</span></div>
        </div>
      `
    },
    {
      title: 'CPU Utilization',
      html: `
        <div class="widget-metric">64%</div>
        <p class="widget-note">Average utilization this hour</p>
        <div class="mini-gauge" aria-hidden="true">
          <div class="mini-gauge-fill" style="--p:64"></div>
        </div>
      `
    }
  ];
</script>

<script lang="ts">
  import '$lib/styles/analytics.css';

  // Key performance indicators displayed in main grid
  const kpis = [
    { label: 'Total Requests (24h)', value: '1,284', delta: '+7.2%' },
    { label: 'Avg Response Time', value: '412 ms', delta: '-5.8%' },
    { label: 'Model Success Rate', value: '98.1%', delta: '+0.6%' },
    { label: 'Escalations', value: '12', delta: '-2 today' }
  ];

  // Hourly activity breakdown table
  const recentActivity = [
    { window: '08:00-09:00', requests: 142, flagged: 2, successRate: '98.6%' },
    { window: '09:00-10:00', requests: 176, flagged: 1, successRate: '99.1%' },
    { window: '10:00-11:00', requests: 221, flagged: 3, successRate: '97.4%' },
    { window: '11:00-12:00', requests: 248, flagged: 4, successRate: '96.9%' },
    { window: '12:00-13:00', requests: 201, flagged: 2, successRate: '98.2%' }
  ];
</script>

<div class="analytics-page">
  <div class="page-header">
    <h1>Analytics</h1>
    <p>
      Live system insights and quick-read widgets styled to match the dashboard shell.
    </p>
  </div>

  <div class="analytics-layout">
    <section class="analytics-main">
      <div class="section-header">
        <h2>Overview</h2>
        <span class="tag">Live</span>
      </div>

      <p class="section-text">
        Main trend area for workload, health, and moderation metrics. The widget bar on the right mirrors these values for quick scanning.
      </p>

      <div class="kpi-grid">
        {#each kpis as kpi}
          <article class="kpi-card">
            <p>{kpi.label}</p>
            <strong>{kpi.value}</strong>
            <span>{kpi.delta}</span>
          </article>
        {/each}
      </div>

      <div class="graph-placeholder">
        <div class="graph-grid" aria-hidden="true"></div>
        <div class="graph-line" aria-hidden="true"></div>
        <div class="graph-label">Detailed analytics graph area</div>
      </div>

      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Window</th>
              <th>Requests</th>
              <th>Flagged</th>
              <th>Success Rate</th>
            </tr>
          </thead>
          <tbody>
            {#each recentActivity as row}
              <tr>
                <td>{row.window}</td>
                <td>{row.requests}</td>
                <td>{row.flagged}</td>
                <td>{row.successRate}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</div>

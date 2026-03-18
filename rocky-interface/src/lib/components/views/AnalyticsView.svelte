<script lang="ts">
  const widgets = [
    {
      title: 'Temperature',
      value: '70°F',
      description: 'Current system temperature'
    },
    {
      title: 'Requests',
      value: '128',
      description: 'Current AI request count'
    },
    {
      title: 'Flagged Requests',
      value: '6',
      description: 'Requests flagged for review'
    },
    {
      title: 'CPU Usage',
      value: '62%',
      description: 'Current CPU utilization'
    }
  ];
</script>

<div class="analytics-page">
  <div class="page-header">
    <h1>Analytics View</h1>
    <p>
      This page shows a larger analytics section with smaller sidebar widgets for quick system summaries.
    </p>
  </div>

  <div class="analytics-layout">
    <section class="analytics-main">
      <div class="section-header">
        <h2>Analytics</h2>
        <span class="tag">Main Panel</span>
      </div>

      <p class="section-text">
        This area is for detailed analytics graphs such as temperature over time, request activity over time, and other system trends.
      </p>

      <div class="graph-placeholder">
        <div class="graph-label">Detailed Analytics Graph Area</div>
      </div>
    </section>

    <aside class="analytics-sidebar">
      <div class="sidebar-header">
        <h2>Quick Widgets</h2>
        <span class="tag">Sidebar</span>
      </div>

      {#each widgets as widget}
        <div class="widget-card">
          <h3>{widget.title}</h3>
          <div class="widget-value">{widget.value}</div>
          <p>{widget.description}</p>
        </div>
      {/each}
    </aside>
  </div>

  <section class="template-section">
    <div class="section-header">
      <h2>Reusable Widget Template</h2>
      <span class="tag">Generic</span>
    </div>

    <p class="section-text">
      Each sidebar widget uses the same card structure with only the title, value, and description changing.
    </p>

    <pre class="template-box">
&lt;div class="widget-card"&gt;
  &lt;h3&gt;Widget Title&lt;/h3&gt;
  &lt;div class="widget-value"&gt;70%&lt;/div&gt;
  &lt;p&gt;Short widget description&lt;/p&gt;
&lt;/div&gt;
    </pre>
  </section>
</div>

<style>
  .analytics-page {
    padding: 24px;
    background: #f4f7fb;
    min-height: 100vh;
    color: #1f2937;
  }

  .page-header {
    margin-bottom: 24px;
  }

  .page-header h1 {
    font-size: 2rem;
    margin-bottom: 8px;
  }

  .page-header p {
    color: #6b7280;
    max-width: 700px;
  }

  .analytics-layout {
    display: grid;
    grid-template-columns: 2.3fr 1fr;
    gap: 20px;
    margin-bottom: 24px;
  }

  .analytics-main,
  .analytics-sidebar,
  .template-section {
    background: white;
    border-radius: 16px;
    padding: 20px;
    box-shadow: 0 6px 18px rgba(17, 24, 39, 0.08);
  }

  .section-header,
  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .section-header h2,
  .sidebar-header h2 {
    font-size: 1.25rem;
    margin: 0;
  }

  .tag {
    background: #e0ecff;
    color: #2457c5;
    font-size: 0.75rem;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 999px;
  }

  .section-text {
    color: #6b7280;
    margin-bottom: 16px;
  }

  .graph-placeholder {
    height: 360px;
    border: 2px dashed #93c5fd;
    background: linear-gradient(180deg, #eff6ff 0%, #ffffff 100%);
    border-radius: 14px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .graph-label {
    color: #2563eb;
    font-weight: 700;
    font-size: 1.1rem;
  }

  .analytics-sidebar {
    display: flex;
    flex-direction: column;
    gap: 14px;
  }

  .widget-card {
    border: 1px solid #e5e7eb;
    border-radius: 14px;
    padding: 16px;
    background: #fafafa;
  }

  .widget-card h3 {
    margin: 0 0 8px 0;
    font-size: 1rem;
    color: #374151;
  }

  .widget-value {
    font-size: 1.8rem;
    font-weight: 700;
    margin-bottom: 6px;
    color: #111827;
  }

  .widget-card p {
    margin: 0;
    color: #6b7280;
    font-size: 0.9rem;
  }

  .template-box {
    background: #111827;
    color: #f9fafb;
    padding: 16px;
    border-radius: 12px;
    overflow-x: auto;
    font-size: 0.9rem;
    line-height: 1.5;
  }

  @media (max-width: 900px) {
    .analytics-layout {
      grid-template-columns: 1fr;
    }
  }
</style><h1>AnalyticsView</h1>

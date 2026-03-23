<script context="module" lang="ts">
  export type HelpWidget = {
    title: string;
    html: string;
  };

  // Widget data synced with right-side widget bar when Help frame is active
  export const helpWidgets: HelpWidget[] = [
    {
      title: 'System Status',
      html: `
        <div class="widget-metric" style="color: #10b981;">Operational</div>
        <p class="widget-note">All systems running normally</p>
      `
    },
    {
      title: 'Quick Contact',
      html: `
        <div class="widget-metric" style="font-size: 1.25rem;">330-672-HELP</div>
        <p class="widget-note">HelpDesk Support Line</p>
        <p class="widget-note">Mon-Fri: 8am - 8pm</p>
      `
    },
    {
      title: 'Maintenance Info',
      html: `
        <div class="widget-metric" style="font-size: 1rem;">1st & 3rd Thursdays</div>
        <p class="widget-note">Scheduled maintenance windows occur from 1:05am to 3:05am ET.</p>
      `
    },
    {
      title: 'Support Tickets',
      html: `
        <div class="widget-metric">0</div>
        <p class="widget-note">Open tickets awaiting response</p>
      `
    }
  ];
</script>

<script lang="ts">
  import '$lib/styles/analytics.css';
  import { currentFrame } from '$lib/stores/frameStore';

  // Replace the '#' with actual routes, external links, and email.
  const resources = [
    { label: 'Kent State FlashLine', description: 'Quick access to your KSU student portal and tools.', action: 'Open FlashLine', href: 'https://flashline.kent.edu', isInternalRoute: false },
    { label: 'Report a Problem', description: 'If the system misbehaves, tell us about it.', action: 'Send an email', href: 'mailto:RockySupport@kent.edu', isInternalRoute: false }, // support email 
    { label: 'Release Notes', description: 'Check out the latest updates and system features.', action: 'View Notes', href: '#release-notes', isInternalRoute: false }, // release notes route
    { label: 'Ready to go?', description: 'Done learning? Head back to the dashboard.', action: 'Back to Dashboard', href: '#', isInternalRoute: true } // internal route
  ];

  // Replace the 'url' values below with paths to files.
  const helpFiles = [
    { title: 'User Management Guide', category: 'Administrators', date: '2026-03-21', status: 'Updated', url: '#' }, // File path 
    { title: 'Course Creation Workflow', category: 'Instructors', date: '2026-02-15', status: 'Current', url: '#' }, // file path 
    { title: 'Analytics Dashboard Overview', category: 'General', date: '2026-01-10', status: 'Current', url: '#' }, // file path 
    { title: 'System Roles & Permissions', category: 'Security', date: '2025-11-28', status: 'Current', url: '#' }, // file path 
    { title: 'Troubleshooting Common Errors', category: 'Support', date: '2026-03-22', status: 'New', url: '#' } // file path 
  ];

  function handleResourceClick(event: MouseEvent, isInternal: boolean) {
    if (isInternal) {
      event.preventDefault(); // Stops the browser from trying to load a URL
      $currentFrame = 'dashboard'; // Tells your app to swap back to the DashboardView
    }
  }
</script>

<div class="analytics-page">
  <div class="page-header">
    <h1>Help Center</h1>
    <p>
      Find answers, browse guides, and connect with support resources.
    </p>
  </div>

  <div class="analytics-layout">
    <section class="analytics-main">
      <div class="section-header">
        <h2>Other Resources</h2>
        <span class="tag">Support</span>
      </div>

      <p class="section-text">
        Quick links to our most commonly used support channels and training materials.
      </p>

      <div class="kpi-grid">
        {#each resources as resource}
          <a 
            href={resource.href} 
            on:click={(e) => handleResourceClick(e, resource.isInternalRoute)}
            class="kpi-card" 
            style="text-decoration: none; color: inherit; display: block; transition: transform 0.2s ease;"
          >
            <p>{resource.label}</p>
            <strong style="font-size: 1rem; margin-top: 0.5rem; display: block; font-weight: 500;">{resource.description}</strong>
            <span style="color: #2563eb; margin-top: 1rem; display: inline-block;">{resource.action} &rarr;</span>
          </a>
        {/each}
      </div>

      <div class="graph-placeholder" style="display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 4rem 2rem; background: #f8fafc; border: 1px dashed #cbd5e1;">
        <h3 style="font-size: 1.5rem; margin-bottom: 0.5rem; color: #0f172a;">Little lost? Try here first!</h3>
        <p style="color: #64748b; margin-bottom: 1.5rem;">Find answers to common questions in our official documentation.</p>
        <button style="background: #2563eb; color: white; border: none; padding: 0.75rem 2rem; border-radius: 99px; font-weight: bold; cursor: pointer; font-size: 1rem;">
          Search the Rocky Guides
        </button>
      </div>

      <div class="section-header" style="margin-top: 2rem;">
        <h2>Documentation</h2>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Document Title</th>
              <th>Category</th>
              <th>Last Updated</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {#each helpFiles as file}
              <tr>
                <td style="font-weight: 500;">
                  <a href={file.url} style="color: #2563eb; text-decoration: none;">
                    📄 {file.title}
                  </a>
                </td>
                <td>{file.category}</td>
                <td>{file.date}</td>
                <td>
                  {#if file.status === 'New'}
                    <span style="background: #dcfce7; color: #166534; padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">NEW</span>
                  {:else if file.status === 'Updated'}
                    <span style="background: #dbeafe; color: #1e40af; padding: 0.1rem 0.5rem; border-radius: 4px; font-size: 0.8rem; font-weight: bold;">UPDATED</span>
                  {:else}
                    <span style="color: #64748b;">{file.status}</span>
                  {/if}
                </td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</div>
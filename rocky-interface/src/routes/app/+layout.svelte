<script>
  import '$lib/styles/app-layout.css';
  import Sidebar from '$lib/components/shell/Sidebar.svelte';
  import Topbar from '$lib/components/shell/Topbar.svelte';
</script>

<Topbar />

<div class="app-shell">
  <Sidebar />

  <main class="app-content">
    <slot />
  </main>
</div>

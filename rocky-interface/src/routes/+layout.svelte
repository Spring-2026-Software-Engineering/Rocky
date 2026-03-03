<script>
	import '$lib/styles/global.css';
	import '$lib/styles/app-layout.css';
	import Sidebar from '$lib/components/shell/Sidebar.svelte';
	import Topbar from '$lib/components/shell/Topbar.svelte';

	import { page } from '$app/state';
	let isRootRoute = $derived(page.url.pathname === '/');

	let { children } = $props();
</script>


<main>
	{#if isRootRoute}
		<Topbar />
		<div class="app-shell">
			<Sidebar />
			<section class="app-content">
				{@render children?.()}
			</section>
		</div>
	{:else}
		{@render children?.()}
	{/if}
</main>

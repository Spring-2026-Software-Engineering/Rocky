<script>
	import '$lib/styles/global.css';
	import '$lib/styles/app-layout.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Topbar from '$lib/components/Topbar.svelte';

	import { page } from '$app/state';
	let isRootRoute = $derived(page.url.pathname === '/');

	let { children, data } = $props();
</script>


<main>
	{#if isRootRoute}
		<Topbar user={data.currentUser} />
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

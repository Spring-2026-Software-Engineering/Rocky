<script>
	import '$lib/styles/global.css';
	import '$lib/styles/app-layout.css';
	import Sidebar from '$lib/components/shell/Sidebar.svelte';
	import Topbar from '$lib/components/shell/Topbar.svelte';

	import { page } from '$app/state';
	let isloginRoute = $derived(page.url.pathname.startsWith('/login'));

	let { children } = $props();
</script>


<main>
	{#if isloginRoute}
		{@render children?.()}
	{:else}
		<Topbar />
		<div class="app-shell">
			<Sidebar />
			<section class="app-content">
				{@render children?.()}
			</section>
		</div>
	{/if}
</main>

<script lang="ts">
	import '$lib/styles/foundation/global.css';
	import '$lib/styles/layout/app-layout.css';
	import Sidebar from '$lib/components/Sidebar.svelte';
	import Topbar from '$lib/components/Topbar.svelte';
	import FeedbackPopup from '$lib/components/FeedbackPopup.svelte';
	import { browser } from '$app/environment';
	import { currentFrame } from '$lib/stores/frameStore';
	import type { FrameName } from '$lib/types/frame';

	import { page } from '$app/state';
	let { children, data } = $props();
	let isRootRoute = $derived(page.url.pathname === '/');
	let initialFrame = $derived(data.initialFrame as FrameName);

	$effect(() => {
		if (browser && initialFrame) {
			currentFrame.set(initialFrame);
		}
	});
</script>


<main>
	<FeedbackPopup />
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

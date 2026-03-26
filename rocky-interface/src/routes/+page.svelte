<script lang="ts">
	import { browser } from '$app/environment';
	import { page } from '$app/state';
	import { currentFrame, frameMap } from '$lib/stores/frameStore';
	import type { FrameName } from '$lib/types/frame';
	import WidgetPanel from '$lib/components/WidgetPanel.svelte';
	import '$lib/styles/foundation/global.css';

	let currentUser = $derived(page.data.currentUser);
	let resolvedFrame = $derived((browser ? $currentFrame : page.data.initialFrame) as FrameName);
	let ActiveView = $derived(frameMap[resolvedFrame]);

	$effect(() => {
		if (browser && !currentUser) {
			window.location.href = '/login';
		}
	});
</script>

{#if currentUser}
	<div class="page-layout">
		<div class="main-content">
			<div class="view-wrapper">
				<ActiveView />
			</div>
		</div>
		<WidgetPanel />
	</div>
{/if}
<script lang="ts">
	import { page } from '$app/state';
	import { currentFrame, frameMap } from '$lib/stores/frameStore';
	import type { FrameName } from '$lib/types/frame';
	import WidgetPanel from '$lib/components/WidgetPanel.svelte';
	import '$lib/styles/global.css';

	let currentUser = $derived(page.data.currentUser);

	$effect(() => {
		if (!currentUser) {
			window.location.href = '/login';
		}
	});
</script>

{#if currentUser}
	<div class="page-layout">
		<div class="main-content">
			<div class="view-wrapper">
				<svelte:component this={frameMap[$currentFrame as FrameName]} />
			</div>
		</div>
		<WidgetPanel />
	</div>
{/if}
<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDefaultWidgets } from '$lib/api/content';
	import WidgetCard from './cards/WidgetCard.svelte';
	import type { PanelWidget } from '$lib/types/widget';

	let widgets: PanelWidget[] = [];
	let error: string | null = null;

	onMount(async () => {
		try {
			widgets = await fetchDefaultWidgets();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading widgets.';
		}
	});
</script>

<div class="widget-panel">

	<h2 class="widget-panel-title">Widgets</h2>

	{#if error}
		<p class="widget-note"><strong>Error:</strong> {error}</p>
	{:else if widgets.length === 0}
		<p class="widget-note">Loading widgets...</p>
	{/if}

	{#each widgets as widget}
		<WidgetCard title={widget.title} html={widget.html ?? ''}>
			{#if !widget.html}
				{#each widget.lines ?? [] as line}
					<p>{line}</p>
				{/each}
			{/if}
		</WidgetCard>
	{/each}

</div>
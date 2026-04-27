<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDefaultWidgets } from '$lib/api/content';
	import WidgetCard from './cards/WidgetCard.svelte';
	import type { PanelWidget } from '$lib/types/widget';

	let widgets: PanelWidget[] = [];
	let error: string | null = null;
	let isLoading = true;
	const widgetHelpArticleUrl = '#';

	onMount(async () => {
		try {
			widgets = await fetchDefaultWidgets();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading widgets.';
		} finally {
			isLoading = false;
		}
	});
</script>

<div class="widget-panel">

	<h2 class="widget-panel-title">Widgets</h2>

	{#if error}
		<p class="widget-note"><strong>Error:</strong> {error}</p>
	{:else if isLoading}
		<p class="widget-note">Loading widgets...</p>
	{:else if widgets.length === 0}
		<p class="widget-note">
			You do not have any widgets yet. Read
			<a class="widget-note-link" href={widgetHelpArticleUrl}>this guide to add and use widgets</a>.
		</p>
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
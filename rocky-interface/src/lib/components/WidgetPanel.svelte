<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchAnalyticsWidgets, fetchDefaultWidgets } from '$lib/api/content';
	import WidgetCard from './cards/WidgetCard.svelte';
	import { currentFrame } from '$lib/stores/frameStore';
	import type { AnalyticsWidget } from '$lib/types/analytics';
	import type { PanelWidget } from '$lib/types/widget';

	let defaultWidgets: PanelWidget[] = [];
	let analyticsWidgets: AnalyticsWidget[] = [];
	let error: string | null = null;

	onMount(async () => {
		try {
			const [loadedDefaultWidgets, loadedAnalyticsWidgets] = await Promise.all([
				fetchDefaultWidgets(),
				fetchAnalyticsWidgets()
			]);

			defaultWidgets = loadedDefaultWidgets;
			analyticsWidgets = loadedAnalyticsWidgets;
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading widgets.';
		}
	});

	$: widgets = $currentFrame === 'analytics' ? analyticsWidgets : defaultWidgets;
	$: panelTitle = $currentFrame === 'analytics' ? 'Analytics Widgets' : 'Widgets';
</script>

<div class="widget-panel">

	<h2 class="widget-panel-title">{panelTitle}</h2>

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
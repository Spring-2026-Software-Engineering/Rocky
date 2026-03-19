<script lang="ts">
	import WidgetCard from './cards/WidgetCard.svelte';
	import { currentFrame, type frameName } from '$lib/stores/frameStore';
	import { analyticsWidgets } from '$lib/components/views/AnalyticsView.svelte';

	type PanelWidget = {
		title: string;
		html?: string;
		lines?: string[];
	};

	const defaultWidgets: PanelWidget[] = [
		{
			title: 'Analytics',
			lines: ['Total System Usage: 98%', 'Active Requests: 42', 'System Temp: 77deg']
		},
		{
			title: 'System Info',
			lines: ['Limit Usage: 88%', 'Courses: 3']
		},
		{
			title: 'Notifications',
			lines: ['No new notifications']
		}
	];

	const frameWidgets: Partial<Record<frameName, PanelWidget[]>> = {
		analytics: analyticsWidgets
	};

	$: widgets = frameWidgets[$currentFrame] ?? defaultWidgets;
	$: panelTitle = $currentFrame === 'analytics' ? 'Analytics Widgets' : 'Widgets';
</script>

<div class="widget-panel">

	<h2 class="widget-panel-title">{panelTitle}</h2>

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
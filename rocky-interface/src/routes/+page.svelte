<script lang="ts">
	import { currentFrame, frameMap, type frameName } from '$lib/stores/frameStore';
	import WidgetPanel from '$lib/components/WidgetPanel.svelte';
	import '$lib/styles/global.css';
	import '$lib/styles/widget-panel.css';
</script>

<div class="page-layout">
	<div class="main-content">
		<svelte:component this={frameMap[$currentFrame as frameName]} />
	</div>
	<WidgetPanel />
</div>
	<script lang="ts">
	import '$lib/styles/sidebar.css';
	import { currentFrame, frameMap, type frameName } from '$lib/stores/frameStore';

	const frames = Object.keys(frameMap) as frameName[];
	const primaryFrames = frames.filter((frame) => frame !== 'help');

	const toLabel = (frame: frameName) => frame.charAt(0).toUpperCase() + frame.slice(1);
</script>

<nav class="sidebar">
	{#each primaryFrames as frame}
		<button class="nav-link" class:active={$currentFrame === (frame as frameName)} on:click={() => currentFrame.set(frame as frameName)}>{toLabel(frame as frameName)}</button>
	{/each}

	<div class="spacer"></div>

	<button class="nav-link" class:active={$currentFrame === 'help'} on:click={() => currentFrame.set('help')}>{toLabel('help')}</button>
</nav>

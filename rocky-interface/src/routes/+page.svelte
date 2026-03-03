<script lang="ts">
	import { currentFrame, frameMap, type frameName } from '$lib/stores/frameStore';
</script>

<svelte:component this={frameMap[$currentFrame as frameName]} />

<script lang="ts">
	export let title: string;
	export let html = '';
</script>

<div class="widget-card">
	<h3>{title}</h3>
	<div class="widget-content">
		{#if html}
			{@html html}
		{:else}
			<slot />
		{/if}
	</div>
</div>
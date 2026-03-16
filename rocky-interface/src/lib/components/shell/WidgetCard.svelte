<script lang="ts">
	export let title: string;
</script>

<div class="widget-card">
	<h3>{title}</h3>
	<div class="widget-content">
		<slot />
	</div>
</div>
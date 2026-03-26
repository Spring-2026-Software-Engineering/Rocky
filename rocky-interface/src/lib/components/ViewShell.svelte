<script lang="ts">
	export let title: string | null = null;

	$: hasActionsSlot = Boolean($$slots.actions);
	$: hasDefaultSlot = Boolean($$slots.default);
	$: hasContentSlot = Boolean($$slots.content);
</script>

<div class="view-header">
	<div class="view-title">
		{#if title}
			<h1>{title}</h1>
		{/if}
	</div>

	{#if hasActionsSlot}
		<div class="view-actions">
			<slot name="actions" />
		</div>
	{/if}
</div>

<div class="view-content">
	{#if hasDefaultSlot}
		<slot />
	{/if}
	{#if hasContentSlot}
		<slot name="content" />
	{/if}
</div>

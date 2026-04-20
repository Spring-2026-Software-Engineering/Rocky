<script lang="ts">
	import { onDestroy } from 'svelte';

	export let title = 'Key Slot';
	export let keyName = '';
	export let hasExistingKey = false;
	export let maskedPreview = '';
	export let placeholderText = 'No key exists for this slot yet.';
	export let generateDisabled = false;
	export let hideDisabled = false;
	export let removeDisabled = false;
	export let onKeyNameChange: (value: string) => void = () => {};
	export let onGenerate: () => Promise<string | null> | string | null = () => null;
	export let onHide: () => void = () => {};
	export let onRemove: () => void = () => {};

	let visibleKey: string | null = null;

	async function handleGenerate() {
		const nextKey = await onGenerate();
		visibleKey = typeof nextKey === 'string' && nextKey.trim() ? nextKey.trim() : null;
	}

	function handleHide() {
		visibleKey = null;
		onHide();
	}

	function handleRemove() {
		visibleKey = null;
		onRemove();
	}

	onDestroy(() => {
		visibleKey = null;
	});
</script>

<div class="course-panel">
	<h3>{title}</h3>
	<div class="course-group-create-row">
		<input
			class="text-input"
			type="text"
			value={keyName}
			placeholder="Key name"
			oninput={(event) => onKeyNameChange((event.currentTarget as HTMLInputElement).value)}
		/>
	</div>
	<p>
		<strong>Key:</strong>
		{#if visibleKey}
			{visibleKey}
		{:else if hasExistingKey}
			{maskedPreview}
		{:else}
			{placeholderText}
		{/if}
	</p>
	<div class="course-inline-actions">
		<button type="button" class="list-go-btn" onclick={handleGenerate} disabled={generateDisabled}>Generate Key</button>
        {#if hasExistingKey || visibleKey}
            <button type="button" class="list-go-btn" onclick={handleRemove} disabled={removeDisabled}>Remove Key</button>
        {/if}
		{#if visibleKey}
			<button type="button" class="list-go-btn" onclick={handleHide} disabled={hideDisabled}>Hide Key</button>
		{/if}
	</div>
</div>

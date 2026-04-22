<script lang="ts">
	import { feedbackMessage } from '$lib/stores/feedbackStore';
	import '$lib/styles/components/modules/feedback-popup.css';
</script>

{#if $feedbackMessage}
	<div class="feedback-popup-layer" aria-live="polite" aria-atomic="true">
		<div
			class="feedback-popup"
			class:feedback-success={$feedbackMessage.kind === 'success'}
			class:feedback-error={$feedbackMessage.kind === 'error'}
			role={$feedbackMessage.kind === 'error' ? 'alert' : 'status'}
		>
			{$feedbackMessage.message}
		</div>
	</div>
{/if}

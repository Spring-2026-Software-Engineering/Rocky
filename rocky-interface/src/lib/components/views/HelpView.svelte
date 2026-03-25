<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchFaqItems } from '$lib/api/content';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import type { FaqItem } from '$lib/types/help';

	let faqItems: FaqItem[] = [];
	let isLoading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			faqItems = await fetchFaqItems();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading FAQ content.';
		} finally {
			isLoading = false;
		}
	});
</script>

<ViewShell title="Help & Support" description="Find answers to common questions and learn how to use the system.">
		<section class="section">
			<div class="section-header">
				<h2>Frequently Asked Questions</h2>
			</div>

			<div class="section-content">
				{#if isLoading}
					<div class="empty-state">
						<p>Loading FAQs...</p>
					</div>
				{:else if error}
					<div class="empty-state">
						<p><strong>Error:</strong> {error}</p>
					</div>
				{:else}
					{#each faqItems as item}
						<div class="faq-item">
							<h3 class="faq-question">{item.question}</h3>
							<p class="faq-answer">
								{item.answer}
							</p>
						</div>
					{/each}
				{/if}
			</div>
		</section>

		<section class="section help-section">
			<div class="section-header">
				<h2>Need More Help?</h2>
			</div>

			<div class="section-content">
				<p class="section-text">
					If you can't find the answer you're looking for, please contact the system administrator or submit a support ticket.
				</p>
				<div class="support-actions">
					<button class="support-btn support-btn-primary">
						Submit Support Ticket
					</button>
					<button class="support-btn support-btn-secondary">
						Email Support
					</button>
				</div>
			</div>
		</section>
</ViewShell>

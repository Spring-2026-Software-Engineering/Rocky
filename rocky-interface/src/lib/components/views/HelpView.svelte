<script lang="ts">
	import ViewShell from '$lib/components/ViewShell.svelte';
	import { currentFrame } from '$lib/stores/frameStore';
	import type { HelpDocument, HelpResource } from '$lib/types/help';

	const resources: HelpResource[] = [
		{
			label: 'Kent State FlashLine',
			description: 'Quick access to your KSU student portal and tools.',
			action: 'Open FlashLine',
			href: 'https://flashline.kent.edu',
			isInternalRoute: false
		},
		{
			label: 'Report a Problem',
			description: 'If the system misbehaves, tell us about it.',
			action: 'Send an email',
			href: 'mailto:RockySupport@kent.edu',
			isInternalRoute: false
		},
		{
			label: 'Release Notes',
			description: 'Check out the latest updates and system features.',
			action: 'View Notes',
			href: '#release-notes',
			isInternalRoute: false
		},
		{
			label: 'Ready to go?',
			description: 'Done learning? Head back to the dashboard.',
			action: 'Back to Dashboard',
			href: '#',
			isInternalRoute: true
		}
	];

	const helpFiles: HelpDocument[] = [
		{ title: 'User Management Guide', category: 'Administrators', date: '2026-03-21', status: 'Updated', url: '#' },
		{ title: 'Course Creation Workflow', category: 'Instructors', date: '2026-02-15', status: 'Current', url: '#' },
		{ title: 'Analytics Dashboard Overview', category: 'General', date: '2026-01-10', status: 'Current', url: '#' },
		{ title: 'System Roles & Permissions', category: 'Security', date: '2025-11-28', status: 'Current', url: '#' },
		{ title: 'Troubleshooting Common Errors', category: 'Support', date: '2026-03-22', status: 'New', url: '#' }
	];

	function handleResourceClick(event: MouseEvent, isInternal: boolean) {
		if (isInternal) {
			event.preventDefault();
			$currentFrame = 'dashboard';
		}
	}
</script>

<ViewShell title="Help Center" description="Find answers, browse guides, and connect with support resources.">
	<section class="section">
		<div class="section-header">
			<h2>Other Resources</h2>
			<span class="tag">Support</span>
		</div>

		<div class="section-content">
			<p class="section-text">Quick links to our most commonly used support channels and training materials.</p>

			<div class="help-resource-grid">
				{#each resources as resource}
					<a href={resource.href} on:click={(e) => handleResourceClick(e, resource.isInternalRoute)} class="help-resource-card">
						<p class="help-resource-label">{resource.label}</p>
						<strong class="help-resource-description">{resource.description}</strong>
						<span class="help-resource-action">{resource.action} -></span>
					</a>
				{/each}
			</div>

			<div class="help-callout">
				<h3 class="help-callout-title">Little lost? Try here first!</h3>
				<p class="help-callout-text">Find answers to common questions in our official documentation.</p>
				<button class="support-btn support-btn-primary" type="button">Search the Rocky Guides</button>
			</div>
		</div>
	</section>

	<section class="section help-section">
		<div class="section-header">
			<h2>Documentation</h2>
		</div>

		<div class="section-content">
			<div class="table-container">
				<table class="data-table">
					<thead>
						<tr>
							<th>Document Title</th>
							<th>Category</th>
							<th>Last Updated</th>
							<th>Status</th>
						</tr>
					</thead>
					<tbody>
						{#each helpFiles as file}
							<tr>
								<td>
									<a href={file.url} class="help-doc-link">{file.title}</a>
								</td>
								<td>{file.category}</td>
								<td>{file.date}</td>
								<td>
									<span
										class="help-status-pill"
										class:help-status-new={file.status === 'New'}
										class:help-status-updated={file.status === 'Updated'}
										class:help-status-current={file.status === 'Current'}
									>
										{file.status}
									</span>
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		</div>
	</section>
</ViewShell>

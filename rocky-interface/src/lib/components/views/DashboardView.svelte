<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchDashboardCourses } from '$lib/api/content';
	import CourseCard from '$lib/components/cards/CourseCard.svelte';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import type { Course } from '$lib/types/course';

	let viewMode: 'card' | 'list' = 'card';
	let showViewMenu = false;
	let courses: Course[] = [];
	let isLoading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			courses = await fetchDashboardCourses();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading courses.';
		} finally {
			isLoading = false;
		}
	});

	function setView(mode: 'card' | 'list') {
		viewMode = mode;
		showViewMenu = false;
	}
</script>

<ViewShell title="Dashboard" description="View and manage all your courses in one place.">
	<div slot="actions" class="view-switcher">
		<button class="view-btn" on:click={() => (showViewMenu = !showViewMenu)}>
			View
			<svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
				<polyline points="6 9 12 15 18 9"></polyline>
			</svg>
		</button>

		{#if showViewMenu}
			<button type="button" class="view-menu-backdrop" aria-label="Close view menu" on:click={() => (showViewMenu = false)}></button>
			<div class="view-menu">
				<button class="view-option" class:active={viewMode === 'card'} on:click={() => setView('card')}>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<rect x="3" y="3" width="7" height="7"></rect>
						<rect x="14" y="3" width="7" height="7"></rect>
						<rect x="14" y="14" width="7" height="7"></rect>
						<rect x="3" y="14" width="7" height="7"></rect>
					</svg>
					Card
				</button>
				<button class="view-option" class:active={viewMode === 'list'} on:click={() => setView('list')}>
					<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<line x1="8" y1="6" x2="21" y2="6"></line>
						<line x1="8" y1="12" x2="21" y2="12"></line>
						<line x1="8" y1="18" x2="21" y2="18"></line>
						<line x1="3" y1="6" x2="3.01" y2="6"></line>
						<line x1="3" y1="12" x2="3.01" y2="12"></line>
						<line x1="3" y1="18" x2="3.01" y2="18"></line>
					</svg>
					List
				</button>
			</div>
		{/if}
	</div>

	{#if isLoading}
		<div class="empty-state">
			<p>Loading courses...</p>
		</div>
	{:else if error}
		<div class="empty-state">
			<p><strong>Error:</strong> {error}</p>
		</div>
	{:else if courses.length === 0}
		<div class="empty-state">
			<p>No courses available.</p>
		</div>
	{:else if viewMode === 'card'}
			<div class="grid grid-3">
				{#each courses as course}
					<CourseCard {course} mode="card" />
				{/each}
			</div>
		{:else}
			<div class="grid grid-1">
				{#each courses as course}
					<CourseCard {course} mode="list" />
				{/each}
			</div>
	{/if}
</ViewShell>


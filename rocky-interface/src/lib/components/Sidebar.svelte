	<script lang="ts">
	import '$lib/styles/components/sidebar.css';
	import { page } from '$app/state';
	import { browser } from '$app/environment';
	import { onDestroy, onMount } from 'svelte';
	import { fetchCourses } from '$lib/api/content';
	import type { Course } from '$lib/types/course';
	import { currentFrame, frameMap } from '$lib/stores/frameStore';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import { toFrameLabel, type FrameName } from '$lib/types/frame';

	const frames = Object.keys(frameMap) as FrameName[];
	const primaryFrames = frames.filter((frame) => frame !== 'help');
	const coursesFrameIndex = primaryFrames.indexOf('courses');
	const framesBeforeCourses = coursesFrameIndex >= 0 ? primaryFrames.slice(0, coursesFrameIndex) : primaryFrames.filter((frame) => frame !== 'courses');
	const framesAfterCourses = coursesFrameIndex >= 0 ? primaryFrames.slice(coursesFrameIndex + 1) : [];
	let activeFrame = $derived((browser ? $currentFrame : page.data.initialFrame) as FrameName);
	const SESSION_VALIDATE_TTL_MS = 10_000;
	let lastSessionValidationAt = 0;
	let sessionValidationInFlight: Promise<boolean> | null = null;
	let courseMenuOpen = $state(false);
	let courseMenuLoading = $state(false);
	let courseMenuError = $state<string | null>(null);
	let visibleCourses = $state<Course[]>([]);
	let courseTabGroupElement: HTMLDivElement | null = null;

	function scrollToTopOfApp() {
		if (!browser) {
			return;
		}

		window.scrollTo({ top: 0, behavior: 'auto' });

		const appContent = document.querySelector('.app-content');
		if (appContent instanceof HTMLElement) {
			appContent.scrollTo({ top: 0, behavior: 'auto' });
		}

		const viewContent = document.querySelector('.view-content');
		if (viewContent instanceof HTMLElement) {
			viewContent.scrollTo({ top: 0, behavior: 'auto' });
		}
	}

	function handleDocumentPointerDown(event: PointerEvent) {
		if (!courseMenuOpen) {
			return;
		}

		const target = event.target;
		if (!(target instanceof Node)) {
			return;
		}

		if (courseTabGroupElement?.contains(target)) {
			return;
		}

		courseMenuOpen = false;
	}

	async function validateSession(): Promise<boolean> {
		if (Date.now() - lastSessionValidationAt < SESSION_VALIDATE_TTL_MS) {
			return true;
		}

		if (sessionValidationInFlight) {
			return sessionValidationInFlight;
		}

		sessionValidationInFlight = (async () => {
			const response = await fetch('/api/session/validate', { method: 'GET', cache: 'no-store' });
			if (!response.ok) {
				return false;
			}

			lastSessionValidationAt = Date.now();
			return true;
		})();

		try {
			return await sessionValidationInFlight;
		} finally {
			sessionValidationInFlight = null;
		}
	}

	async function handleFrameChange(frame: FrameName) {
		if ($currentFrame === frame) {
			return;
		}

		try {
			const isValid = await validateSession();
			if (!isValid) {
				window.location.href = '/login';
				return;
			}

			currentFrame.set(frame);
		} catch (error) {
			console.error('Session validation error:', error);
			window.location.href = '/login';
		}
	}

	async function loadCourseMenuData() {
		courseMenuLoading = true;
		courseMenuError = null;

		try {
			visibleCourses = await fetchCourses();
		} catch (error) {
			courseMenuError = error instanceof Error ? error.message : 'Unable to load your courses right now.';
		} finally {
			courseMenuLoading = false;
		}
	}

	onMount(() => {
		void loadCourseMenuData();
		if (browser) {
			document.addEventListener('pointerdown', handleDocumentPointerDown, true);
		}
	});

	onDestroy(() => {
		if (browser) {
			document.removeEventListener('pointerdown', handleDocumentPointerDown, true);
		}
	});

	async function toggleCourseMenu() {
		if (!courseMenuOpen && visibleCourses.length === 0 && !courseMenuError) {
			await loadCourseMenuData();
		}

		courseMenuOpen = !courseMenuOpen;
	}

	async function openCourse(courseId: number) {
		selectedCourseId.set(courseId);
		await handleFrameChange('courses');
		courseMenuOpen = false;
		requestAnimationFrame(() => {
			requestAnimationFrame(() => {
				scrollToTopOfApp();
			});
		});
	}
</script>

<nav class="sidebar">
	{#each framesBeforeCourses as frame}
		<button class="nav-link" class:active={activeFrame === frame} onclick={() => handleFrameChange(frame)}>{toFrameLabel(frame)}</button>
	{/each}

	<div class="course-tab-group" bind:this={courseTabGroupElement}>
		<button class="nav-link" class:active={activeFrame === 'courses'} onclick={toggleCourseMenu}>{toFrameLabel('courses')}</button>
		{#if courseMenuOpen}
			<div class="course-popout" role="menu" aria-label="Course list">
				<div class="course-popout-header">Courses</div>
				{#if courseMenuLoading}
					<p class="course-popout-state">Loading courses...</p>
				{:else if courseMenuError}
					<p class="course-popout-state">{courseMenuError}</p>
				{:else if visibleCourses.length === 0}
					<p class="course-popout-state">No courses found in the database.</p>
				{:else}
					<div class="course-popout-list">
						{#each visibleCourses as course}
							<button type="button" class="course-popout-item" class:active={$selectedCourseId === course.id} onclick={() => openCourse(course.id)}>
								<span class="course-dot" style={`background-color: ${course.color};`}></span>
								<span class="course-item-text">
									<span class="course-item-name">{course.name}</span>
									<span class="course-item-meta">{course.code}</span>
								</span>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	{#each framesAfterCourses as frame}
		<button class="nav-link" class:active={activeFrame === frame} onclick={() => handleFrameChange(frame)}>{toFrameLabel(frame)}</button>
	{/each}

	<div class="spacer"></div>

	<button class="nav-link" class:active={activeFrame === 'help'} onclick={() => handleFrameChange('help')}>{toFrameLabel('help')}</button>
</nav>

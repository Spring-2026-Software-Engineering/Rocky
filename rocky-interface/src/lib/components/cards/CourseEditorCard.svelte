<script lang="ts">
	import { createEventDispatcher } from 'svelte';
	import {
		COURSE_EDITOR_SEMESTER_TERMS,
		COURSE_EDITOR_SEMESTER_YEAR_MAX,
		COURSE_EDITOR_SEMESTER_YEAR_MIN
	} from '$lib/config/courseEditor';
	import type { User } from '$lib/types/user';

	type CourseEditorForm = {
		name: string;
		code: string;
		semester: string;
		instructorId: string;
	};

	export let title = 'Course';
	export let submitLabel = 'Save';
	export let form: CourseEditorForm;
	export let users: User[] = [];
	export let idPrefix = 'course-editor';
	export let useSemesterPicker = false;
	export let semesterYearMin = COURSE_EDITOR_SEMESTER_YEAR_MIN;
	export let semesterYearMax = COURSE_EDITOR_SEMESTER_YEAR_MAX;
	export let semesterTerms: string[] = COURSE_EDITOR_SEMESTER_TERMS;

	let selectedSemesterTerm = 'none';
	let selectedSemesterYear = COURSE_EDITOR_SEMESTER_YEAR_MIN;
	let lastParsedSemester = '';

	const dispatch = createEventDispatcher<{ submit: void }>();

	function clampSemesterYear(value: number): number {
		if (!Number.isFinite(value)) {
			return semesterYearMin;
		}
		if (value < semesterYearMin) {
			return semesterYearMin;
		}
		if (value > semesterYearMax) {
			return semesterYearMax;
		}
		return Math.floor(value);
	}

	function toSemesterTitle(value: string): string {
		if (!value) {
			return '';
		}
		return `${value.charAt(0).toUpperCase()}${value.slice(1)}`;
	}

	function parseSemester(semesterValue: string): { term: string; year: number } {
		const fallbackYear = clampSemesterYear(new Date().getFullYear());
		const normalized = semesterValue.trim();
		if (!normalized) {
			return { term: 'none', year: fallbackYear };
		}
		if (normalized.toLowerCase() === 'none') {
			return { term: 'none', year: fallbackYear };
		}

		const [termRaw, yearRaw] = normalized.split(/\s+/, 2);
		const term = (termRaw || '').trim().toLowerCase();
		const parsedYear = Number(yearRaw);

		return {
			term: semesterTerms.includes(term) ? term : 'none',
			year: clampSemesterYear(parsedYear)
		};
	}

	function updateSemesterFromControls() {
		if (!useSemesterPicker) {
			return;
		}

		if (selectedSemesterTerm === 'none') {
			form.semester = 'None';
			lastParsedSemester = form.semester;
			return;
		}

		selectedSemesterYear = clampSemesterYear(selectedSemesterYear);
		form.semester = `${toSemesterTitle(selectedSemesterTerm)} ${selectedSemesterYear}`.trim();
		lastParsedSemester = form.semester;
	}

	$: if (useSemesterPicker && form.semester !== lastParsedSemester) {
		const parsed = parseSemester(form.semester);
		selectedSemesterTerm = parsed.term;
		selectedSemesterYear = parsed.year;
		lastParsedSemester = form.semester;
	}

	$: if (useSemesterPicker && !semesterTerms.includes(selectedSemesterTerm)) {
		selectedSemesterTerm = 'none';
		updateSemesterFromControls();
	}

	$: if (useSemesterPicker && selectedSemesterTerm === 'none') {
		selectedSemesterYear = clampSemesterYear(selectedSemesterYear);
	}

	function submitForm() {
		if (useSemesterPicker) {
			updateSemesterFromControls();
		}
		dispatch('submit');
	}
</script>

<div class="course-panel">
	<h3>{title}</h3>
	<div class="course-edit-grid">
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-name-input`}>Course Name</label>
			<input id={`${idPrefix}-name-input`} class="text-input" type="text" bind:value={form.name} required />
		</div>
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-code-input`}>Course ID</label>
			<input id={`${idPrefix}-code-input`} class="text-input" type="text" bind:value={form.code} placeholder="Optional" />
		</div>
		{#if useSemesterPicker}
			<div class="form-group">
				<label class="form-label" for={`${idPrefix}-semester-term-select`}>Semester</label>
				<div class="course-semester-row">
					<select
						id={`${idPrefix}-semester-term-select`}
						class="text-input"
						bind:value={selectedSemesterTerm}
						onchange={updateSemesterFromControls}
					>
						{#each semesterTerms as term}
							<option value={term}>{toSemesterTitle(term)}</option>
						{/each}
					</select>
					<input
						id={`${idPrefix}-semester-year-input`}
						class="text-input"
						type="number"
						min={semesterYearMin}
						max={semesterYearMax}
						bind:value={selectedSemesterYear}
						disabled={selectedSemesterTerm === 'none'}
						class:is-disabled={selectedSemesterTerm === 'none'}
						onchange={updateSemesterFromControls}
					/>
				</div>
			</div>
		{:else}
			<div class="form-group">
				<label class="form-label" for={`${idPrefix}-semester-input`}>Semester</label>
				<input id={`${idPrefix}-semester-input`} class="text-input" type="text" bind:value={form.semester} />
			</div>
		{/if}
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-instructor-select`}>Instructor</label>
			<select id={`${idPrefix}-instructor-select`} class="text-input" bind:value={form.instructorId}>
				<option value="">None</option>
				{#each users as user}
					<option value={user.id}>{user.displayName} ({user.id})</option>
				{/each}
			</select>
		</div>
	</div>
	<div class="course-edit-actions">
		<button type="button" class="view-btn" onclick={submitForm}>{submitLabel}</button>
	</div>
</div>

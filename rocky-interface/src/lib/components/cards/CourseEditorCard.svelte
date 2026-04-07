<script lang="ts">
	import { createEventDispatcher } from 'svelte';
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

	const dispatch = createEventDispatcher<{ submit: void }>();

	function submitForm() {
		dispatch('submit');
	}
</script>

<div class="course-panel">
	<h3>{title}</h3>
	<div class="course-edit-grid">
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-name-input`}>Course Name</label>
			<input id={`${idPrefix}-name-input`} class="text-input" type="text" bind:value={form.name} />
		</div>
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-code-input`}>Course ID</label>
			<input id={`${idPrefix}-code-input`} class="text-input" type="text" bind:value={form.code} />
		</div>
		<div class="form-group">
			<label class="form-label" for={`${idPrefix}-semester-input`}>Semester</label>
			<input id={`${idPrefix}-semester-input`} class="text-input" type="text" bind:value={form.semester} />
		</div>
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

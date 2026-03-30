<script lang="ts">
	import { onMount } from 'svelte';
	import { currentFrame } from '$lib/stores/frameStore';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import { fetchUsersForViews } from '$lib/api/users';
	import CourseEditorCard from '$lib/components/cards/CourseEditorCard.svelte';
	import {
		closeCourseComposer,
		courseComposerState,
		createdCourseDraft
	} from '$lib/stores/courseComposerStore';
	import type { User } from '$lib/types/user';
	import type { Course } from '$lib/types/course';

	let users: User[] = [];
	let form = {
		name: '',
		code: '',
		semester: '',
		instructorEmail: ''
	};

	onMount(async () => {
		try {
			users = await fetchUsersForViews();
		} catch (error) {
			console.error('Unable to load users for course composer', error);
		}
	});

	$: accountUsers = users.filter((user) => user.email && user.email.trim() && user.email !== 'N/A');
	$: if ($courseComposerState.isOpen) {
		form = {
			name: '',
			code: '',
			semester: '',
			instructorEmail: ''
		};
	}

	function createCourseFromForm() {
		const normalizedInstructorEmail = form.instructorEmail.trim().toLowerCase();
		const selectedInstructor = accountUsers.find((user) => user.email.toLowerCase() === normalizedInstructorEmail);
		const instructorDisplayName = selectedInstructor?.name || 'None';
		const created: Course = {
			id: Date.now(),
			name: form.name.trim() || 'Untitled Course',
			code: form.code.trim() || 'TBD 0000',
			semester: form.semester.trim() || '',
			instructor: instructorDisplayName,
			color: '#1a4a8a'
		};

		console.info('[pseudo-api] create-course', {
			course: {
				name: created.name,
				code: created.code,
				semester: created.semester,
				instructor: created.instructor,
				instructorEmail: normalizedInstructorEmail || null
			}
		});

		createdCourseDraft.set(created);
		selectedCourseId.set(created.id);
		currentFrame.set('courses');
		closeCourseComposer();
	}
</script>

{#if $courseComposerState.isOpen}
	<div
		class="course-composer-layer"
		role="presentation"
		tabindex="-1"
		onclick={closeCourseComposer}
		onkeydown={(event) => {
			if (event.key === 'Escape' || event.key === 'Enter' || event.key === ' ') {
				closeCourseComposer();
			}
		}}
	>
		<div
			class="course-composer-popout"
			role="dialog"
			aria-modal="true"
			aria-label="Create Course"
			tabindex="0"
			onclick={(event) => event.stopPropagation()}
			onkeydown={(event) => event.stopPropagation()}
		>
			<div class="course-composer-title-row">
				<h3>Create Course</h3>
				<button type="button" class="list-go-btn" onclick={closeCourseComposer}>Close</button>
			</div>
			<CourseEditorCard
				title="Course Details"
				submitLabel="Create Course"
				idPrefix="global-create-course"
				users={accountUsers}
				form={form}
				on:submit={createCourseFromForm}
			/>
		</div>
	</div>
{/if}

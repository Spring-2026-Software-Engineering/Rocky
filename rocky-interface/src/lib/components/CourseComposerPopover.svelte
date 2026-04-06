<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import { createCourse } from '$lib/api/courses';
	import { currentFrame } from '$lib/stores/frameStore';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import { fetchUsersForViews } from '$lib/api/users';
	import CourseEditorCard from '$lib/components/cards/CourseEditorCard.svelte';
	import { closeCourseComposer, courseComposerState } from '$lib/stores/courseComposerStore';
	import type { User } from '$lib/types/user';

	let users: User[] = [];
	let form = {
		name: '',
		code: '',
		semester: '',
		instructorEmail: ''
	};

	onMount(async () => {
		try {
			if ($page.data.currentUser?.role?.toLowerCase() === 'admin') {
				users = await fetchUsersForViews();
			}
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

	async function createCourseFromForm() {
		const normalizedInstructorEmail = form.instructorEmail.trim().toLowerCase();
		const created = await createCourse({
			name: form.name.trim() || 'Untitled Course',
			code: form.code.trim() || 'TBD 0000',
			semester: form.semester.trim() || '',
			instructorEmail: normalizedInstructorEmail,
			instructorName: accountUsers.find((user) => user.email.toLowerCase() === normalizedInstructorEmail)?.name
		});

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

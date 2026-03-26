<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchCourseDetails, fetchCourses } from '$lib/api/content';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import type { Course, CourseDetail } from '$lib/types/course';

	type CourseTab = 'home' | 'edit-courses' | 'edit-people' | 'graphs';

	let allCourses: Course[] = [];
	let visibleCourses: Course[] = [];
	let detailsByCourseId: Record<number, CourseDetail> = {};
	let activeTab: CourseTab = 'home';
	let isLoading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			const [courses, details] = await Promise.all([fetchCourses(), fetchCourseDetails()]);
			allCourses = courses;
			visibleCourses = courses;
			detailsByCourseId = Object.fromEntries(details.map((detail) => [detail.id, detail]));

			if ($selectedCourseId === null && visibleCourses.length > 0) {
				selectedCourseId.set(visibleCourses[0].id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading course data.';
		} finally {
			isLoading = false;
		}
	});

	$: visibleCourses = allCourses;
	$: selectedCourse = visibleCourses.find((course) => course.id === $selectedCourseId) ?? null;
	$: selectedDetail = selectedCourse ? detailsByCourseId[selectedCourse.id] : null;
	$: availableTabs = ['home', 'edit-courses', 'edit-people', 'graphs'] as CourseTab[];
	$: if (!availableTabs.includes(activeTab)) {
		activeTab = 'home';
	}

	function removeMember(memberId: string) {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		detailsByCourseId = {
			...detailsByCourseId,
			[selectedCourse.id]: {
				...selectedDetail,
				members: selectedDetail.members.filter((member) => member.id !== memberId)
			}
		};
	}

	function addMember() {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		const name = prompt('Enter member name:');
		if (!name?.trim()) {
			return;
		}

		const email = prompt('Enter member email:')?.trim() || 'unknown@kent.edu';
		const roleInput = prompt('Role (instructor or student):')?.trim().toLowerCase() || 'student';
		const memberRole = roleInput === 'instructor' ? 'instructor' : 'student';
		const generatedId = `m-${Date.now()}`;

		detailsByCourseId = {
			...detailsByCourseId,
			[selectedCourse.id]: {
				...selectedDetail,
				members: [
					...selectedDetail.members,
					{
						id: generatedId,
						name: name.trim(),
						email,
						role: memberRole
					}
				]
			}
		};
	}
</script>

<ViewShell title="Courses">
	{#if isLoading}
		<div class="empty-state">
			<p>Loading course workspace...</p>
		</div>
	{:else if error}
		<div class="empty-state">
			<p><strong>Error:</strong> {error}</p>
		</div>
	{:else if visibleCourses.length === 0}
		<div class="empty-state">
			<p>No courses were found in the database.</p>
		</div>
	{:else if !selectedCourse}
		<section class="section">
			<div class="section-header">
				<h2>Select a Course</h2>
			</div>
			<div class="section-content">
				<p class="section-text">Choose a course from Dashboard cards or from the Courses tab popout list.</p>
			</div>
		</section>
	{:else}
		<section class="section course-workspace">
			<div class="section-header course-header">
				<div>
					<h2>{selectedCourse.name}</h2>
					<p class="section-text">{selectedCourse.code} · {selectedCourse.semester} · {selectedCourse.instructor}</p>
				</div>
			</div>

			<div class="course-tab-bar">
				{#each availableTabs as tab}
					<button type="button" class="view-btn" class:course-tab-active={activeTab === tab} on:click={() => (activeTab = tab)}>
						{tab === 'home' ? 'Home' : tab === 'edit-courses' ? 'Edit Courses' : tab === 'edit-people' ? 'Edit People' : 'Graphs'}
					</button>
				{/each}
			</div>

			{#if activeTab === 'home'}
				<div class="section-content course-content-grid">
					<div class="course-panel">
						<h3>Course Snapshot</h3>
						<p><strong>Code:</strong> {selectedCourse.code}</p>
						<p><strong>Semester:</strong> {selectedCourse.semester}</p>
						<p><strong>Instructor:</strong> {selectedCourse.instructor}</p>
					</div>
					<div class="course-panel">
						<h3>Enrollment</h3>
						<p><strong>Total members:</strong> {selectedDetail?.members.length || 0}</p>
						<p><strong>Instructors:</strong> {selectedDetail?.members.filter((member) => member.role === 'instructor').length || 0}</p>
						<p><strong>Students:</strong> {selectedDetail?.members.filter((member) => member.role === 'student').length || 0}</p>
					</div>
				</div>
			{:else if activeTab === 'edit-courses'}
				<div class="section-content course-content-grid">
					<div class="course-panel">
						<h3>Course Metadata</h3>
						<p><strong>Code:</strong> {selectedCourse.code}</p>
						<p><strong>Instructor:</strong> {selectedCourse.instructor}</p>
						<p><strong>Semester:</strong> {selectedCourse.semester}</p>
					</div>
					<div class="course-panel">
						<h3>Enrollment Snapshot</h3>
						<p><strong>Total members:</strong> {selectedDetail?.members.length || 0}</p>
						<p><strong>Instructors:</strong> {selectedDetail?.members.filter((member) => member.role === 'instructor').length || 0}</p>
						<p><strong>Students:</strong> {selectedDetail?.members.filter((member) => member.role === 'student').length || 0}</p>
					</div>
				</div>
			{:else if activeTab === 'edit-people'}
				<div class="section-content">
					<div class="course-people-actions">
						<button type="button" class="view-btn" on:click={addMember}>Add Person</button>
					</div>
					<div class="table-container">
						<table class="data-table">
							<thead>
								<tr>
									<th>Name</th>
									<th>Email</th>
									<th>Role</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{#if selectedDetail?.members.length}
									{#each selectedDetail.members as member}
										<tr>
											<td>{member.name}</td>
											<td>{member.email}</td>
											<td>{member.role}</td>
											<td><button type="button" class="list-go-btn" on:click={() => removeMember(member.id)}>Remove</button></td>
										</tr>
									{/each}
								{:else}
									<tr>
										<td colspan="4">No members in this course yet.</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				</div>
			{:else}
				<div class="section-content course-content-grid">
					<div class="course-panel">
						<h3>Engagement Summary</h3>
						<p><strong>Active members:</strong> {selectedDetail?.members.length || 0}</p>
					</div>
					<div class="course-panel">
						<h3>Course Data Source</h3>
						<p>Course shell information is loaded from the database course list.</p>
						<p>Member records are loaded from the course detail dataset.</p>
					</div>
				</div>
			{/if}
		</section>
	{/if}
</ViewShell>

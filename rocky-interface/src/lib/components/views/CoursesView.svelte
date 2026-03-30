<script lang="ts">
	import { onMount } from 'svelte';
	import { currentUser } from '$lib/stores/authStore';
	import { fetchCourseDetails, fetchCourseGroups, fetchCourses } from '$lib/api/content';
	import { fetchUsersForViews } from '$lib/api/users';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import { createdCourseDraft } from '$lib/stores/courseComposerStore';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import CourseEditorCard from '$lib/components/cards/CourseEditorCard.svelte';
	import type { Course, CourseDetail, CourseGroup } from '$lib/types/course';
	import type { User } from '$lib/types/user';

	type CourseTab = 'home' | 'edit-course' | 'edit-people' | 'groups';

	let allCourses: Course[] = [];
	let allUsers: User[] = [];
	let visibleCourses: Course[] = [];
	let detailsByCourseId: Record<number, CourseDetail> = {};
	let groupsByCourseId: Record<number, CourseGroup[]> = {};
	let activeTab: CourseTab = 'home';
	let isLoading = true;
	let error: string | null = null;
	let editCourseForm = {
		name: '',
		code: '',
		semester: '',
		instructorEmail: ''
	};
	let newGroupName = '';
	let pendingGroupMemberEmailByGroupId: Record<string, string> = {};
	let importCsvInput: HTMLInputElement | null = null;

	onMount(async () => {
		try {
			const [courses, details, groups, users] = await Promise.all([
				fetchCourses(),
				fetchCourseDetails(),
				fetchCourseGroups(),
				fetchUsersForViews()
			]);
			allCourses = courses;
			allUsers = users;
			visibleCourses = courses;
			detailsByCourseId = Object.fromEntries(details.map((detail) => [detail.id, detail]));
			groupsByCourseId = groups.reduce<Record<number, CourseGroup[]>>((acc, group) => {
				const existing = acc[group.courseId] || [];
				acc[group.courseId] = [...existing, group];
				return acc;
			}, {});

			if ($selectedCourseId === null && visibleCourses.length > 0) {
				selectedCourseId.set(visibleCourses[0].id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading course data.';
		} finally {
			isLoading = false;
		}
	});

	$: visibleCourses = $createdCourseDraft
		? [$createdCourseDraft, ...allCourses.filter((course) => course.id !== $createdCourseDraft?.id)]
		: allCourses;
	$: selectedCourse = visibleCourses.find((course) => course.id === $selectedCourseId) ?? null;
	$: selectedDetail = selectedCourse ? detailsByCourseId[selectedCourse.id] : null;
	$: selectedGroups = selectedCourse ? groupsByCourseId[selectedCourse.id] || [] : [];
	$: nonAdminUsers = allUsers.filter((user) => user.role !== 'admin');
	$: accountUsers = allUsers.filter((user) => user.email && user.email.trim() && user.email !== 'N/A');
	$: currentUserEmail = $currentUser?.email?.trim().toLowerCase() || '';
	$: currentUserRole = $currentUser?.role?.trim().toLowerCase() || '';
	$: instructorEmailForCourse = selectedDetail?.members.find((member) => member.role === 'instructor')?.email?.toLowerCase() || '';
	$: isCurrentUserAdmin = currentUserRole === 'admin';
	$: isCurrentUserCourseInstructor = currentUserEmail !== '' && currentUserEmail === instructorEmailForCourse;
	$: studentGroup = currentUserEmail
		? selectedGroups.find((group) => group.memberEmails.includes(currentUserEmail)) || null
		: null;
	$: studentGroupMembers = (() => {
		if (!studentGroup || !selectedDetail) {
			return [];
		}

		const memberByEmail = new Map(selectedDetail.members.map((member) => [member.email.trim().toLowerCase(), member]));
		return studentGroup.memberEmails
			.map((email) => memberByEmail.get(email))
			.filter((member): member is NonNullable<typeof member> => Boolean(member))
			.filter((member) => member.role === 'student');
	})();
	$: canShowStudentGroupPanel = !isCurrentUserAdmin && !isCurrentUserCourseInstructor && Boolean(studentGroup);
	$: selectableGroupMembers = (selectedDetail?.members || []).filter((member) => member.role !== 'instructor');
	$: availableTabs = ['home', 'edit-course', 'edit-people', 'groups'] as CourseTab[];
	$: if (!availableTabs.includes(activeTab)) {
		activeTab = 'home';
	}
	$: if (selectedCourse) {
		const matchingUserByName = nonAdminUsers.find((user) => user.name === selectedCourse.instructor);
		const courseInstructorMember = selectedDetail?.members.find((member) => member.role === 'instructor');
		editCourseForm = {
			name: selectedCourse.name,
			code: selectedCourse.code,
			semester: selectedCourse.semester,
			instructorEmail: (courseInstructorMember?.email || matchingUserByName?.email || '').toLowerCase()
		};
	}

	function sendPseudoRequest(action: string, payload: unknown) {
		console.info(`[pseudo-api] ${action}`, payload);
	}

	function removeMember(memberId: string) {
		if (!selectedCourse || !selectedDetail) {
			return;
		}
		sendPseudoRequest('remove-course-member', {
			courseId: selectedCourse.id,
			memberId
		});
	}

	function addMemberByEmailPrompt() {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		const emailInput = window.prompt('Enter email to add to this course:');
		const email = emailInput?.trim().toLowerCase() || '';
		if (!email) {
			return;
		}

		sendPseudoRequest('add-course-member', {
			courseId: selectedCourse.id,
			member: {
				id: email,
				email,
				role: 'student'
			}
		});
	}

	async function importPeopleFromCanvasCsv(event: Event) {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		const target = event.currentTarget as HTMLInputElement | null;
		const file = target?.files?.[0];
		if (!file) {
			return;
		}

		const csvText = await file.text();
		const emailMatches = csvText.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi) || [];
		const parsedEmails = [...new Set(emailMatches.map((value) => value.trim().toLowerCase()))];
		if (parsedEmails.length === 0) {
			target.value = '';
			return;
		}

		sendPseudoRequest('bulk-import-course-members', {
			courseId: selectedCourse.id,
			source: 'canvas-csv',
			fileName: file.name,
			emails: parsedEmails
		});

		target.value = '';
	}

	function triggerCsvImportPicker() {
		importCsvInput?.click();
	}

	function saveCourseEdits() {
		if (!selectedCourse) {
			return;
		}

		const normalizedInstructorEmail = editCourseForm.instructorEmail.trim().toLowerCase();
		const selectedInstructor = accountUsers.find((user) => user.email.toLowerCase() === normalizedInstructorEmail);
		const instructorDisplayName = selectedInstructor?.name || 'None';

		sendPseudoRequest('update-course-metadata', {
			courseId: selectedCourse.id,
			updates: {
				name: editCourseForm.name.trim() || selectedCourse.name,
				code: editCourseForm.code.trim() || selectedCourse.code,
				semester: editCourseForm.semester.trim() || selectedCourse.semester,
				instructor: instructorDisplayName,
				instructorEmail: normalizedInstructorEmail || null
			}
		});
	}

	function createGroup() {
		if (!selectedCourse) {
			return;
		}

		const trimmedName = newGroupName.trim();
		if (!trimmedName) {
			return;
		}

		sendPseudoRequest('create-course-group', {
			courseId: selectedCourse.id,
			groupName: trimmedName
		});
		newGroupName = '';
	}

	function addGroupMember(groupId: string) {
		if (!selectedCourse) {
			return;
		}

		const email = (pendingGroupMemberEmailByGroupId[groupId] || '').trim().toLowerCase();
		if (!email) {
			return;
		}

		sendPseudoRequest('add-group-member', {
			courseId: selectedCourse.id,
			groupId,
			email
		});
		pendingGroupMemberEmailByGroupId = {
			...pendingGroupMemberEmailByGroupId,
			[groupId]: ''
		};
	}

	function removeGroupMember(groupId: string, email: string) {
		if (!selectedCourse) {
			return;
		}

		sendPseudoRequest('remove-group-member', {
			courseId: selectedCourse.id,
			groupId,
			email
		});
	}

	function getAvailableMembersForGroup(group: CourseGroup) {
		return selectableGroupMembers.filter((member) => !group.memberEmails.includes(member.email.toLowerCase()));
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
					<button type="button" class="view-btn" class:course-tab-active={activeTab === tab} onclick={() => (activeTab = tab)}>
						{tab === 'home' ? 'Home' : tab === 'edit-course' ? 'Edit Course' : tab === 'edit-people' ? 'Edit People' : 'Groups'}
					</button>
				{/each}
			</div>

			{#if activeTab === 'home'}
				<div class="section-content home-panel-stack">
					<div class="course-panel">
						<h3>Course API Key</h3>
						<div class="course-row-split">
							<div>
								<p><strong>Key:</strong> ****</p>
							</div>
							<div class="course-inline-actions">
								<button type="button" class="list-go-btn" onclick={() => sendPseudoRequest('regenerate-course-api-key', { courseId: selectedCourse.id })}>Regenerate</button>
								<button type="button" class="list-go-btn" onclick={() => sendPseudoRequest('delete-course-api-key', { courseId: selectedCourse.id })}>Delete</button>
							</div>
						</div>
					</div>
					{#if canShowStudentGroupPanel && studentGroup}
						<div class="course-panel">
							<h3>Your Group</h3>
							<p><strong>{studentGroup.name}</strong></p>
							<ul class="course-inline-list">
								{#each studentGroupMembers as member}
									<li>{member.name} ({member.email})</li>
								{/each}
							</ul>
						</div>
					{/if}
					<div class="course-panel">
						<h3>Personal API Data</h3>
						<p><strong>Status:</strong> Awaiting backend response fields.</p>
					</div>
				</div>
			{:else if activeTab === 'edit-course'}
				<div class="section-content">
					<CourseEditorCard
						title="Edit Course"
						submitLabel="Save Course"
						idPrefix="edit-course"
						users={accountUsers}
						form={editCourseForm}
						on:submit={saveCourseEdits}
					/>
				</div>
			{:else if activeTab === 'edit-people'}
				<div class="section-content">
					<div class="course-people-actions">
						<button type="button" class="view-btn" onclick={addMemberByEmailPrompt}>Add Person</button>
						<button type="button" class="view-btn" onclick={triggerCsvImportPicker}>Import Canvas CSV</button>
						<input
							class="course-hidden-input"
							type="file"
							accept=".csv,text/csv"
							bind:this={importCsvInput}
							onchange={importPeopleFromCanvasCsv}
						/>
					</div>
					<div class="table-container">
						<table class="data-table course-people-table">
							<colgroup>
								<col />
								<col />
								<col />
								<col class="course-table-actions-col" />
							</colgroup>
							<thead>
								<tr>
									<th>Name</th>
									<th>Email</th>
									<th>Role</th>
									<th class="table-actions-head">Actions</th>
								</tr>
							</thead>
							<tbody>
								{#if selectedDetail?.members.length}
									{#each selectedDetail.members as member}
										<tr>
											<td>{member.name}</td>
											<td>{member.email}</td>
											<td>{member.role}</td>
											<td class="table-actions-cell"><button type="button" class="list-go-btn" onclick={() => removeMember(member.id)}>Remove</button></td>
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
				<div class="section-content">
					<div class="course-people-actions">
						<div class="course-group-create-row">
							<input class="text-input" type="text" bind:value={newGroupName} placeholder="New group name" />
							<button type="button" class="view-btn" onclick={createGroup}>Create Group</button>
						</div>
					</div>
					<div class="table-container">
						<table class="data-table group-table">
							<colgroup>
								<col class="group-col-name" />
								<col class="group-col-members" />
								<col class="group-col-add" />
							</colgroup>
							<thead>
								<tr>
									<th>Group Name</th>
									<th>Members</th>
									<th>Add User</th>
								</tr>
							</thead>
							<tbody>
								{#if selectedGroups.length}
									{#each selectedGroups as group}
										<tr>
											<td>{group.name}</td>
											<td>
												{#if group.memberEmails.length}
													<ul class="course-inline-list">
														{#each group.memberEmails as email}
															<li>
																{email}
																<button type="button" class="list-go-btn" onclick={() => removeGroupMember(group.id, email)}>Remove</button>
															</li>
														{/each}
													</ul>
												{:else}
													No members assigned.
												{/if}
											</td>
											<td>
												<div class="course-group-add-row">
													<select
														class="text-input"
														value={pendingGroupMemberEmailByGroupId[group.id] || ''}
														onchange={(event) => {
															const target = event.currentTarget as HTMLSelectElement;
															pendingGroupMemberEmailByGroupId = {
																...pendingGroupMemberEmailByGroupId,
																[group.id]: target.value
															};
														}}
													>
														<option value="">Select course member</option>
														{#each getAvailableMembersForGroup(group) as member}
															<option value={member.email}>{member.name} ({member.email})</option>
														{/each}
													</select>
													<button type="button" class="list-go-btn" onclick={() => addGroupMember(group.id)}>Add</button>
												</div>
											</td>
										</tr>
									{/each}
								{:else}
									<tr>
										<td colspan="3">No groups found for this course yet.</td>
									</tr>
								{/if}
							</tbody>
						</table>
					</div>
				</div>
			{/if}

		</section>
	{/if}
</ViewShell>

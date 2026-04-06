<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		addCourseMembers,
		addGroupMember as addCourseGroupMember,
		createCourseGroup as createCourseGroupRequest,
		fetchCourseApiHistory,
		removeCourseMember,
		removeGroupMember as removeCourseGroupMember,
		updateCourseMetadata
	} from '$lib/api/courses';
	import { fetchCourseDetails, fetchCourseGroups, fetchCourses } from '$lib/api/content';
	import { fetchUsersForViews } from '$lib/api/users';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import CourseEditorCard from '$lib/components/cards/CourseEditorCard.svelte';
	import type { Course, CourseDetail, CourseGroup } from '$lib/types/course';
	import type { User } from '$lib/types/user';
	import type { CourseApiHistoryEntry } from '$lib/api/courses';

	type CourseTab = 'home' | 'edit-course' | 'edit-people' | 'groups';

	let allCourses: Course[] = [];
	let allUsers: User[] = [];
	let baseVisibleCourses: Course[] = [];
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
	let previewApiKey: string | null = null;
	let courseApiHistory: CourseApiHistoryEntry[] = [];
	let courseApiHistoryLoading = false;
	let courseApiHistoryError: string | null = null;
	let loadedCourseApiHistoryForId: number | null = null;

	async function loadWorkspace() {
		try {
			const requestList = [fetchCourses(), fetchCourseDetails(), fetchCourseGroups()] as const;
			const [courses, details, groups] = await Promise.all(requestList);
			const needsUsers = $page.data.currentUser?.role?.toLowerCase() === 'admin';
			const usersPromise = needsUsers ? fetchUsersForViews() : Promise.resolve([] as User[]);
			const users = await usersPromise;

			allCourses = courses;
			allUsers = users;
			detailsByCourseId = Object.fromEntries(details.map((detail) => [detail.id, detail]));
			groupsByCourseId = groups.reduce<Record<number, CourseGroup[]>>((acc, group) => {
				const existing = acc[group.courseId] || [];
				acc[group.courseId] = [...existing, group];
				return acc;
			}, {});

			if ($selectedCourseId === null && courses.length > 0) {
				selectedCourseId.set(courses[0].id);
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred while loading course data.';
		} finally {
			isLoading = false;
		}
	}

	onMount(async () => {
		await loadWorkspace();
	});

	$: visibleCourses = baseVisibleCourses;
	$: selectedCourse = visibleCourses.find((course) => course.id === $selectedCourseId) ?? null;
	$: selectedDetail = selectedCourse ? detailsByCourseId[selectedCourse.id] : null;
	$: selectedGroups = selectedCourse ? groupsByCourseId[selectedCourse.id] || [] : [];
	$: nonAdminUsers = allUsers.filter((user) => user.role !== 'admin');
	$: accountUsers = allUsers.filter((user) => user.email && user.email.trim() && user.email !== 'N/A');
	$: currentUserEmail = $page.data.currentUser?.email?.trim().toLowerCase() || '';
	$: currentUserRole = $page.data.currentUser?.role?.trim().toLowerCase() || '';
	$: isCurrentUserAdmin = currentUserRole === 'admin';
	$: baseVisibleCourses = isCurrentUserAdmin
		? allCourses
		: allCourses.filter((course) => {
				const members = detailsByCourseId[course.id]?.members || [];
				return members.some((member) => member.email.toLowerCase() === currentUserEmail);
		  });
	$: instructorEmailForCourse = selectedDetail?.members.find((member) => member.role === 'instructor')?.email?.toLowerCase() || '';
	$: isCurrentUserCourseInstructor = currentUserEmail !== '' && currentUserEmail === instructorEmailForCourse;
	$: isCurrentUserClient = currentUserRole === 'client';
	$: canEditCourse = isCurrentUserAdmin;
	$: canEditPeopleAndGroups = isCurrentUserAdmin || isCurrentUserCourseInstructor;
	$: studentGroup = currentUserEmail
		? selectedGroups.find((group) => group.memberEmails.includes(currentUserEmail)) || null
		: null;
	$: studentMembers = (selectedDetail?.members || []).filter((member) => member.role === 'student');
	$: groupedStudentEmailSet = new Set(
		selectedGroups.flatMap((group) => group.memberEmails.map((email) => email.trim().toLowerCase()))
	);
	$: ungroupedStudentMembers = studentMembers.filter((member) => !groupedStudentEmailSet.has(member.email.trim().toLowerCase()));
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
	$: memberByEmail = new Map((selectedDetail?.members || []).map((member) => [member.email.trim().toLowerCase(), member]));
	$: groupMembershipRows = selectedGroups.map((group) => ({
		group,
		members: group.memberEmails
			.map((email) => memberByEmail.get(email.trim().toLowerCase()))
			.filter((member): member is NonNullable<typeof member> => Boolean(member))
			.filter((member) => member.role === 'student')
	}));
	$: canViewManagerApiData = isCurrentUserAdmin || isCurrentUserCourseInstructor;
	$: canViewCourseApiHistory = isCurrentUserAdmin;
	$: canViewPersonalApiData = isCurrentUserClient && !isCurrentUserCourseInstructor && !studentGroup;
	$: showCourseTabBar = canEditCourse || canEditPeopleAndGroups;
	$: selectableGroupMembers = (selectedDetail?.members || []).filter((member) => member.role !== 'instructor');
	$: availableTabs = [
		'home',
		...(canEditCourse ? (['edit-course'] as CourseTab[]) : []),
		...(canEditPeopleAndGroups ? (['edit-people', 'groups'] as CourseTab[]) : [])
	] as CourseTab[];
	$: if (!availableTabs.includes(activeTab)) {
		activeTab = 'home';
	}
	$: if (!selectedCourse && visibleCourses.length > 0) {
		selectedCourseId.set(visibleCourses[0].id);
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
	$: if (selectedCourse && canViewCourseApiHistory && loadedCourseApiHistoryForId !== selectedCourse.id) {
		void loadCourseApiHistory(selectedCourse.id);
	}

	async function refreshAfterWrite() {
		isLoading = true;
		loadedCourseApiHistoryForId = null;
		await loadWorkspace();
	}

	async function loadCourseApiHistory(courseId: number) {
		courseApiHistoryLoading = true;
		courseApiHistoryError = null;
		loadedCourseApiHistoryForId = courseId;

		try {
			courseApiHistory = await fetchCourseApiHistory(courseId);
		} catch (err) {
			courseApiHistoryError = err instanceof Error ? err.message : 'Unable to load API history.';
			courseApiHistory = [];
		} finally {
			courseApiHistoryLoading = false;
		}
	}

	async function removeMember(memberId: string) {
		if (!selectedCourse || !selectedDetail) {
			return;
		}
		await removeCourseMember(selectedCourse.id, memberId);
		await refreshAfterWrite();
	}

	async function addMemberByEmailPrompt() {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		const emailInput = window.prompt('Enter email to add to this course:');
		const email = emailInput?.trim().toLowerCase() || '';
		if (!email) {
			return;
		}

		await addCourseMembers(selectedCourse.id, [{ email, role: 'student' }]);
		await refreshAfterWrite();
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

		await addCourseMembers(
			selectedCourse.id,
			parsedEmails.map((email) => ({ email, role: 'student' }))
		);
		await refreshAfterWrite();

		target.value = '';
	}

	function triggerCsvImportPicker() {
		importCsvInput?.click();
	}

	async function saveCourseEdits() {
		if (!selectedCourse) {
			return;
		}

		const normalizedInstructorEmail = editCourseForm.instructorEmail.trim().toLowerCase();
		const currentInstructorEmail = selectedDetail?.members.find((member) => member.role === 'instructor')?.email?.toLowerCase() || '';
		await updateCourseMetadata(selectedCourse.id, {
			name: editCourseForm.name.trim() || selectedCourse.name,
			code: editCourseForm.code.trim() || selectedCourse.code,
			semester: editCourseForm.semester.trim() || selectedCourse.semester,
			instructorEmail: normalizedInstructorEmail || currentInstructorEmail
		});
		await refreshAfterWrite();
	}

	async function createGroup() {
		if (!selectedCourse) {
			return;
		}

		const trimmedName = newGroupName.trim();
		if (!trimmedName) {
			return;
		}

		await createCourseGroupRequest(selectedCourse.id, trimmedName);
		await refreshAfterWrite();
		newGroupName = '';
	}

	async function addGroupMember(groupId: string) {
		if (!selectedCourse) {
			return;
		}

		const email = (pendingGroupMemberEmailByGroupId[groupId] || '').trim().toLowerCase();
		if (!email) {
			return;
		}

		await addCourseGroupMember(selectedCourse.id, groupId, email);
		await refreshAfterWrite();
		pendingGroupMemberEmailByGroupId = {
			...pendingGroupMemberEmailByGroupId,
			[groupId]: ''
		};
	}

	async function removeGroupMember(groupId: string, email: string) {
		if (!selectedCourse) {
			return;
		}

		await removeCourseGroupMember(selectedCourse.id, groupId, email);
		await refreshAfterWrite();
	}

	async function regenerateApiKey() {
		if (!selectedCourse) {
			return;
		}

		console.info('[pseudo-api] generate-course-api-key', { courseId: selectedCourse.id });
		previewApiKey = 'working on implmentation';
	}

	function clearPreviewApiKey() {
		previewApiKey = null;
	}

	async function deleteApiKey() {
		if (!selectedCourse) {
			return;
		}

		console.info('[pseudo-api] delete-course-api-key', { courseId: selectedCourse.id });
		previewApiKey = null;
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

			{#if showCourseTabBar}
				<div class="course-tab-bar">
					{#each availableTabs as tab}
						<button type="button" class="view-btn" class:course-tab-active={activeTab === tab} onclick={() => (activeTab = tab)}>
							{tab === 'home' ? 'Home' : tab === 'edit-course' ? 'Edit Course' : tab === 'edit-people' ? 'Edit People' : 'Groups'}
						</button>
					{/each}
				</div>
			{/if}

			{#if activeTab === 'home'}
				<div class="section-content home-panel-stack">
					{#if !isCurrentUserCourseInstructor}
						<div class="course-panel">
							<h3>Course API Key</h3>
							<div class="course-row-split">
								<div>
									<p><strong>Preview Key:</strong> {previewApiKey || 'working on implmentation'}</p>
								</div>
								<div class="course-inline-actions">
									<button type="button" class="list-go-btn" onclick={regenerateApiKey}>Generate API Key</button>
									<button type="button" class="list-go-btn" onclick={clearPreviewApiKey}>Clear Preview</button>
								</div>
							</div>
						</div>
					{/if}
					{#if isCurrentUserClient && studentGroup}
						<div class="course-panel">
							<h3>Group API Data</h3>
							<p><strong>{studentGroup.name}</strong></p>
							<ul class="course-inline-list">
								{#each studentGroupMembers as member}
									<li>{member.name} ({member.email}) - API data pending implementation.</li>
								{/each}
							</ul>
						</div>
					{/if}
					{#if canViewManagerApiData}
						<div class="course-panel">
							<h3>Student API Data</h3>
							{#if ungroupedStudentMembers.length}
								<ul class="course-inline-list">
									{#each ungroupedStudentMembers as member}
										<li>{member.name} ({member.email}) - API data pending implementation.</li>
									{/each}
								</ul>
							{:else}
								<p>No ungrouped students found for this course.</p>
							{/if}
						</div>
						<div class="course-panel">
							<h3>Group API Data</h3>
							{#if groupMembershipRows.length}
								{#each groupMembershipRows as row}
									<p><strong>{row.group.name}:</strong> {row.members.length ? row.members.map((member) => member.name).join(', ') : 'No student members'} - API data pending implementation.</p>
								{/each}
							{:else}
								<p>No groups found for this course.</p>
							{/if}
						</div>
					{/if}
					{#if canViewCourseApiHistory}
						<div class="course-panel">
							<h3>API History</h3>
							{#if courseApiHistoryLoading}
								<p>Loading API history...</p>
							{:else if courseApiHistoryError}
								<p><strong>Error:</strong> {courseApiHistoryError}</p>
							{:else if courseApiHistory.length === 0}
								<p>No API history has been recorded for this course yet.</p>
							{:else}
								<ul class="course-inline-list">
									{#each courseApiHistory as entry}
										<li>
											<strong>{entry.userEmail}</strong> · {entry.eventType} · {entry.groupName ? `Group: ${entry.groupName}` : 'Ungrouped'} · {entry.created || 'pending timestamp'}
										</li>
									{/each}
								</ul>
							{/if}
						</div>
					{/if}
					{#if canViewPersonalApiData}
						<div class="course-panel">
							<h3>Personal API Data</h3>
							<p><strong>Status:</strong> Awaiting backend response fields.</p>
						</div>
					{/if}
				</div>
			{:else if activeTab === 'edit-course' && canEditCourse}
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
			{:else if activeTab === 'edit-people' && canEditPeopleAndGroups}
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
															{@const member = memberByEmail.get(email.trim().toLowerCase())}
															<li>
																{member?.name || email} ({email})
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

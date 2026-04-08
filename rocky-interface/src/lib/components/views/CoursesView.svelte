<script lang="ts">
	import { onMount } from 'svelte';
	import { page } from '$app/stores';
	import {
		addCourseMembers,
		addGroupMember as addCourseGroupMember,
		createCourseGroup as createCourseGroupRequest,
		deleteCourseApiKey,
		fetchCourseApiKeys,
		fetchCourseApiHistory,
		removeCourseMember,
		removeGroupMember as removeCourseGroupMember,
		regenerateCourseApiKey,
		updateCourseGroupKeyLimit,
		updateCourseMemberKeyLimit,
		updateCourseMetadata
	} from '$lib/api/courses';
	import { fetchCourseDetails, fetchCourseGroups, fetchCourses } from '$lib/api/content';
	import { fetchUsersForViews } from '$lib/api/users';
	import { selectedCourseId } from '$lib/stores/courseStore';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import CourseEditorCard from '$lib/components/cards/CourseEditorCard.svelte';
	import type { Course, CourseApiKeySummary, CourseDetail, CourseGroup } from '$lib/types/course';
	import type { User } from '$lib/types/user';
	import type { CourseApiHistoryEntry, CourseApiKeySummaryResponse } from '$lib/api/courses';

	type CourseTab = 'home' | 'edit-course' | 'edit-people' | 'groups';
	const API_KEY_PREFIX = 'sk_kent_';

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
		instructorId: ''
	};
	let newGroupName = '';
	let pendingGroupMemberIdByGroupId: Record<string, string> = {};
	let importCsvInput: HTMLInputElement | null = null;
	let previewApiKey: string | null = null;
	let apiKeyActionError: string | null = null;
	let courseApiHistory: CourseApiHistoryEntry[] = [];
	let courseApiHistoryLoading = false;
	let courseApiHistoryError: string | null = null;
	let loadedCourseApiHistoryForId: number | null = null;
	let lastSelectedCourseId: number | null = null;
	let courseApiKeys: CourseApiKeySummary[] = [];
	let courseApiKeysLoading = false;
	let courseApiKeysError: string | null = null;
	let loadedCourseApiKeysForId: number | null = null;
	let newPersonalKeyName = '';
	let newGroupKeyNameByGroupId: Record<string, string> = {};
	let pendingMemberKeyLimitById: Record<string, number> = {};
	let pendingGroupKeyLimitById: Record<string, number> = {};

	async function loadWorkspace() {
		try {
			const requestList = [fetchCourses(), fetchCourseDetails(), fetchCourseGroups()] as const;
			const [courses, details, groups] = await Promise.all(requestList);
			const needsUsers = Boolean($page.data.currentUser?.isAdmin);
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
	$: selectedGroupIds = new Set(selectedGroups.map((group) => group.id));
	$: nonAdminUsers = allUsers.filter((user) => !user.isAdmin);
	$: accountUsers = allUsers.filter((user) => user.email && user.email.trim() && user.email !== 'N/A');
	$: currentUserId = $page.data.currentUser?.id?.trim() || '';
	$: isCurrentUserAdmin = Boolean($page.data.currentUser?.isAdmin);
	$: baseVisibleCourses = isCurrentUserAdmin
		? allCourses
		: allCourses.filter((course) => {
				const members = detailsByCourseId[course.id]?.members || [];
				return members.some((member) => member.id === currentUserId);
		  });
	$: instructorIdForCourse = selectedDetail?.members.find((member) => member.role === 'instructor')?.id || '';
	$: isCurrentUserCourseInstructor = currentUserId !== '' && currentUserId === instructorIdForCourse;
	$: isCurrentUserClient = !isCurrentUserAdmin;
	$: canEditCourse = isCurrentUserAdmin;
	$: canEditPeopleAndGroups = isCurrentUserAdmin || isCurrentUserCourseInstructor;
	$: studentGroup = currentUserId
		? selectedGroups.find((group) => group.memberIds.includes(currentUserId)) || null
		: null;
	$: studentMembers = (selectedDetail?.members || []).filter((member) => member.role === 'student');
	$: groupedStudentIdSet = new Set(
		selectedGroups.flatMap((group) => group.memberIds.map((id) => id.trim()))
	);
	$: ungroupedStudentMembers = studentMembers.filter((member) => !groupedStudentIdSet.has(member.id));
	$: studentGroupMembers = (() => {
		if (!studentGroup || !selectedDetail) {
			return [];
		}

		const memberById = new Map(selectedDetail.members.map((member) => [member.id, member]));
		return studentGroup.memberIds
			.map((id) => memberById.get(id))
			.filter((member): member is NonNullable<typeof member> => Boolean(member))
			.filter((member) => member.role === 'student');
	})();
	$: memberById = new Map((selectedDetail?.members || []).map((member) => [member.id, member]));
	$: groupMembershipRows = selectedGroups.map((group) => ({
		group,
		members: group.memberIds
			.map((id) => memberById.get(id.trim()))
			.filter((member): member is NonNullable<typeof member> => Boolean(member))
			.filter((member) => member.role === 'student')
	}));
	$: canViewManagerApiData = isCurrentUserAdmin || isCurrentUserCourseInstructor;
	$: canViewCourseApiHistory = isCurrentUserAdmin;
	$: canViewPersonalApiData = isCurrentUserClient && !isCurrentUserCourseInstructor && !studentGroup;
	$: personalOwnedKeys = courseApiKeys.filter(
		(key) => key.ownerType === 'person' && key.ownerId === currentUserId
	);
	$: groupOwnedKeys = courseApiKeys.filter(
		(key) => key.ownerType === 'group' && selectedGroupIds.has(key.ownerId)
	);
	$: canGenerateApiKey = Boolean(
		selectedCourse &&
		(isCurrentUserAdmin || (selectedDetail?.members || []).some((member) => member.id === currentUserId))
	);
	$: hasExistingApiKey = Boolean(selectedCourse?.hasApiKey);
	$: currentUserIsApiKeyOwner = selectedCourse?.apiKeyOwnerType === 'person' && selectedCourse?.apiKeyOwnerId === currentUserId;
	$: currentUserIsApiKeyGroupMember =
		selectedCourse?.apiKeyOwnerType === 'group' &&
		Boolean(
			selectedCourse.apiKeyOwnerId &&
			selectedGroups.some((group) => group.id === selectedCourse.apiKeyOwnerId && group.memberIds.includes(currentUserId))
		);
	$: shouldShowMaskedApiKey = hasExistingApiKey && (isCurrentUserAdmin || currentUserIsApiKeyOwner || currentUserIsApiKeyGroupMember);
	$: maskedApiKeyPreview = shouldShowMaskedApiKey ? `${API_KEY_PREFIX}${'*'.repeat(17)}` : null;
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
		const matchingUserByName = nonAdminUsers.find((user) => user.displayName === selectedCourse.instructor);
		const courseInstructorMember = selectedDetail?.members.find((member) => member.role === 'instructor');
		editCourseForm = {
			name: selectedCourse.name,
			code: selectedCourse.code,
			semester: selectedCourse.semester,
			instructorId: courseInstructorMember?.id || matchingUserByName?.id || ''
		};
	}
	$: if (selectedCourse && canViewCourseApiHistory && loadedCourseApiHistoryForId !== selectedCourse.id) {
		void loadCourseApiHistory(selectedCourse.id);
	}
	$: if (selectedCourse && loadedCourseApiKeysForId !== selectedCourse.id) {
		void loadCourseApiKeys(selectedCourse.id);
	}
	$: if (selectedCourse?.id && selectedCourse.id !== lastSelectedCourseId) {
		lastSelectedCourseId = selectedCourse.id;
		apiKeyActionError = null;
		previewApiKey = null;
		newPersonalKeyName = '';
		newGroupKeyNameByGroupId = {};
		pendingMemberKeyLimitById = {};
		pendingGroupKeyLimitById = {};
	}

	function setSelectedCourseHasApiKey(
		hasApiKey: boolean,
		keyState?: {
			apiKeyOwnerType?: 'person' | 'group' | null;
			apiKeyOwnerId?: string | null;
			apiKeyGroupCreatedBy?: string | null;
			apiKeyCreated?: string | null;
		}
	) {
		if (!selectedCourse) {
			return;
		}

		allCourses = allCourses.map((course) =>
			course.id === selectedCourse.id
				? {
						...course,
						hasApiKey,
						apiKeyOwnerType: keyState?.apiKeyOwnerType ?? null,
						apiKeyOwnerId: keyState?.apiKeyOwnerId ?? null,
						apiKeyGroupCreatedBy: keyState?.apiKeyGroupCreatedBy ?? null,
						apiKeyCreated: keyState?.apiKeyCreated ?? null
				  }
				: course
		);
	}

	async function refreshAfterWrite() {
		isLoading = true;
		loadedCourseApiHistoryForId = null;
		loadedCourseApiKeysForId = null;
		await loadWorkspace();
	}

	function normalizeApiKeySummaries(rawKeys: CourseApiKeySummaryResponse[]): CourseApiKeySummary[] {
		return rawKeys
			.map((entry) => ({
				ownerType: (entry.owner_type === 'group' ? 'group' : 'person') as 'person' | 'group',
				ownerId: entry.owner_id?.trim() || '',
				keyName: entry.key_name?.trim() || 'key-1',
				created: entry.created?.trim() || '',
				courseId: typeof entry.course_id === 'number' ? entry.course_id : selectedCourse?.id || 0
			}))
			.filter((entry) => entry.ownerId.length > 0 && entry.keyName.length > 0);
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

	async function loadCourseApiKeys(courseId: number) {
		courseApiKeysLoading = true;
		courseApiKeysError = null;
		loadedCourseApiKeysForId = courseId;

		try {
			const rawKeys = await fetchCourseApiKeys(courseId);
			courseApiKeys = normalizeApiKeySummaries(rawKeys);
		} catch (err) {
			courseApiKeysError = err instanceof Error ? err.message : 'Unable to load API keys.';
			courseApiKeys = [];
		} finally {
			courseApiKeysLoading = false;
		}
	}

	async function removeMember(memberId: string) {
		if (!selectedCourse || !selectedDetail) {
			return;
		}
		await removeCourseMember(selectedCourse.id, memberId);
		await refreshAfterWrite();
	}

	async function addMemberByIdPrompt() {
		if (!selectedCourse || !selectedDetail) {
			return;
		}

		const idInput = window.prompt('Enter user id to add to this course:');
		const id = idInput?.trim() || '';
		if (!id) {
			return;
		}

		await addCourseMembers(selectedCourse.id, [{ id, role: 'student' }]);
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
		const idMatches = csvText.match(/(?:KSUID|WLID)\d{9}/gi) || [];
		const parsedIds = [...new Set(idMatches.map((value) => value.trim()))];
		if (parsedIds.length === 0) {
			target.value = '';
			return;
		}

		await addCourseMembers(
			selectedCourse.id,
			parsedIds.map((id) => ({ id, role: 'student' }))
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

		const normalizedInstructorId = editCourseForm.instructorId.trim();
		const currentInstructorId = selectedDetail?.members.find((member) => member.role === 'instructor')?.id || '';
		await updateCourseMetadata(selectedCourse.id, {
			name: editCourseForm.name.trim() || selectedCourse.name,
			code: editCourseForm.code.trim() || selectedCourse.code,
			semester: editCourseForm.semester.trim() || selectedCourse.semester,
			instructorId: normalizedInstructorId || currentInstructorId
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

		const id = (pendingGroupMemberIdByGroupId[groupId] || '').trim();
		if (!id) {
			return;
		}

		await addCourseGroupMember(selectedCourse.id, groupId, id);
		await refreshAfterWrite();
		pendingGroupMemberIdByGroupId = {
			...pendingGroupMemberIdByGroupId,
			[groupId]: ''
		};
	}

	async function removeGroupMember(groupId: string, id: string) {
		if (!selectedCourse) {
			return;
		}

		await removeCourseGroupMember(selectedCourse.id, groupId, id);
		await refreshAfterWrite();
	}

	async function regenerateApiKey() {
		if (!selectedCourse) {
			return;
		}

		try {
			apiKeyActionError = null;
			const response = await regenerateCourseApiKey(selectedCourse.id, {
				ownerType: 'person',
				ownerId: currentUserId,
				keyName: 'key-1'
			});
			previewApiKey = response.api_key?.trim() || null;
			setSelectedCourseHasApiKey(true, {
				apiKeyOwnerType: response.owner_type ?? null,
				apiKeyOwnerId: response.owner_id ?? null,
				apiKeyGroupCreatedBy: response.group_created_by ?? null,
				apiKeyCreated: response.created ?? null
			});
			await loadCourseApiKeys(selectedCourse.id);
		} catch (err) {
			apiKeyActionError = err instanceof Error ? err.message : 'Unable to generate API key.';
		}
	}

	async function generateNamedPersonalKey() {
		if (!selectedCourse || !currentUserId) {
			return;
		}
		const keyName = newPersonalKeyName.trim() || `key-${personalOwnedKeys.length + 1}`;
		try {
			apiKeyActionError = null;
			const response = await regenerateCourseApiKey(selectedCourse.id, {
				ownerType: 'person',
				ownerId: currentUserId,
				keyName
			});
			previewApiKey = response.api_key?.trim() || null;
			newPersonalKeyName = '';
			await loadCourseApiKeys(selectedCourse.id);
		} catch (err) {
			apiKeyActionError = err instanceof Error ? err.message : 'Unable to generate personal key.';
		}
	}

	async function generateNamedGroupKey(groupId: string) {
		if (!selectedCourse) {
			return;
		}
		const keyName = (newGroupKeyNameByGroupId[groupId] || '').trim() || `key-${groupOwnedKeys.filter((key) => key.ownerId === groupId).length + 1}`;
		try {
			apiKeyActionError = null;
			const response = await regenerateCourseApiKey(selectedCourse.id, {
				ownerType: 'group',
				groupId,
				keyName
			});
			previewApiKey = response.api_key?.trim() || null;
			newGroupKeyNameByGroupId = {
				...newGroupKeyNameByGroupId,
				[groupId]: ''
			};
			await loadCourseApiKeys(selectedCourse.id);
		} catch (err) {
			apiKeyActionError = err instanceof Error ? err.message : 'Unable to generate group key.';
		}
	}

	async function saveMemberKeyLimit(memberId: string) {
		if (!selectedCourse) {
			return;
		}
		const keyLimit = pendingMemberKeyLimitById[memberId];
		if (!Number.isInteger(keyLimit) || keyLimit < 1) {
			return;
		}
		await updateCourseMemberKeyLimit(selectedCourse.id, memberId, keyLimit);
		await refreshAfterWrite();
	}

	async function saveGroupKeyLimit(groupId: string) {
		if (!selectedCourse) {
			return;
		}
		const keyLimit = pendingGroupKeyLimitById[groupId];
		if (!Number.isInteger(keyLimit) || keyLimit < 1) {
			return;
		}
		await updateCourseGroupKeyLimit(selectedCourse.id, groupId, keyLimit);
		await refreshAfterWrite();
	}

	function clearPreviewApiKey() {
		previewApiKey = null;
	}

	async function deleteApiKey() {
		if (!selectedCourse) {
			return;
		}

		try {
			apiKeyActionError = null;
			await deleteCourseApiKey(selectedCourse.id);
			previewApiKey = null;
			setSelectedCourseHasApiKey(false, {
				apiKeyOwnerType: null,
				apiKeyOwnerId: null,
				apiKeyGroupCreatedBy: null,
				apiKeyCreated: null
			});
		} catch (err) {
			apiKeyActionError = err instanceof Error ? err.message : 'Unable to delete API key.';
		}
	}

	function getAvailableMembersForGroup(group: CourseGroup) {
		return selectableGroupMembers.filter((member) => !group.memberIds.includes(member.id));
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
					<div class="course-panel">
						<h3>API Key Workspace</h3>
						<div class="course-row-split">
							<div>
								<p>
									<strong>Latest Generated Key:</strong>
									{#if previewApiKey}
										{previewApiKey}
									{:else if maskedApiKeyPreview}
										{maskedApiKeyPreview}
									{:else}
										Generate a key to view it once.
									{/if}
								</p>
								{#if previewApiKey}
									<p>Save this key now! This key will not be saved on reload.</p>
								{/if}
								{#if courseApiKeysLoading}
									<p>Loading key cards...</p>
								{:else if courseApiKeysError}
									<p><strong>Error:</strong> {courseApiKeysError}</p>
								{/if}
								{#if apiKeyActionError}
									<p class="course-key-error"><strong>Error:</strong> {apiKeyActionError}</p>
								{/if}
							</div>
							<div class="course-inline-actions">
									{#if canGenerateApiKey && !isCurrentUserAdmin}
									<button type="button" class="list-go-btn" onclick={regenerateApiKey}>Generate API Key</button>
									{/if}
									{#if isCurrentUserAdmin && hasExistingApiKey}
										<button type="button" class="list-go-btn" onclick={deleteApiKey}>Delete API Key</button>
									{/if}
								{#if previewApiKey}
									<button type="button" class="list-go-btn" onclick={clearPreviewApiKey}>Hide Key</button>
								{/if}
							</div>
						</div>
					</div>
					<div class="course-panel">
						<h3>Personal Keys</h3>
						{#if !currentUserId}
							<p>Sign in to manage personal keys.</p>
						{:else}
							<div class="course-group-create-row">
								<input class="text-input" type="text" bind:value={newPersonalKeyName} placeholder="New personal key name" />
								<button type="button" class="view-btn" onclick={generateNamedPersonalKey}>Generate Personal Key</button>
							</div>
							{#if personalOwnedKeys.length === 0}
								<p>No personal keys yet.</p>
							{:else}
								<ul class="course-inline-list">
									{#each personalOwnedKeys as key}
										<li><strong>{key.keyName}</strong> · {API_KEY_PREFIX}{'*'.repeat(17)} · {key.created || 'pending timestamp'}</li>
									{/each}
								</ul>
							{/if}
						{/if}
					</div>
					<div class="course-panel">
						<h3>Group Keys</h3>
						{#if selectedGroups.filter((group) => group.memberIds.includes(currentUserId)).length === 0}
							<p>You are not in a course group for this class.</p>
						{:else}
							{#each selectedGroups.filter((group) => group.memberIds.includes(currentUserId)) as group}
								<p><strong>{group.name}</strong></p>
								<div class="course-group-create-row">
									<input class="text-input" type="text" bind:value={newGroupKeyNameByGroupId[group.id]} placeholder="New group key name" />
									<button type="button" class="view-btn" onclick={() => generateNamedGroupKey(group.id)}>Generate Group Key</button>
								</div>
								<ul class="course-inline-list">
									{#each groupOwnedKeys.filter((key) => key.ownerId === group.id) as key}
										<li><strong>{key.keyName}</strong> · {API_KEY_PREFIX}{'*'.repeat(17)} · {key.created || 'pending timestamp'}</li>
									{/each}
								</ul>
							{/each}
						{/if}
					</div>
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
											<strong>{entry.userId}</strong> · {entry.eventType} · {entry.groupName ? `Group: ${entry.groupName}` : 'Ungrouped'} · {entry.created || 'pending timestamp'}
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
						<button type="button" class="view-btn" onclick={addMemberByIdPrompt}>Add Person</button>
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
								<col />
								<col class="course-table-actions-col" />
							</colgroup>
							<thead>
								<tr>
									<th>Name</th>
									<th>Email</th>
									<th>Role</th>
									<th>Keys</th>
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
											<td>
												<div class="course-group-add-row">
													<input
														class="text-input"
														type="number"
														min="1"
														value={pendingMemberKeyLimitById[member.id] ?? member.keyLimit}
														onchange={(event) => {
															const target = event.currentTarget as HTMLInputElement;
															pendingMemberKeyLimitById = {
																...pendingMemberKeyLimitById,
																[member.id]: Math.max(1, Number(target.value) || 1)
															};
														}}
													/>
													<button type="button" class="list-go-btn" onclick={() => saveMemberKeyLimit(member.id)}>Save</button>
												</div>
											</td>
											<td class="table-actions-cell"><button type="button" class="list-go-btn" onclick={() => removeMember(member.id)}>Remove</button></td>
										</tr>
									{/each}
								{:else}
									<tr>
										<td colspan="5">No members in this course yet.</td>
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
								<col class="group-col-add" />
							</colgroup>
							<thead>
								<tr>
									<th>Group Name</th>
									<th>Members</th>
									<th>Keys</th>
									<th>Add User</th>
								</tr>
							</thead>
							<tbody>
								{#if selectedGroups.length}
									{#each selectedGroups as group}
										<tr>
											<td>{group.name}</td>
											<td>
												{#if group.memberIds.length}
													<ul class="course-inline-list">
														{#each group.memberIds as memberId}
															{@const member = memberById.get(memberId.trim())}
															<li>
																{member?.name || memberId} ({memberId})
																<button type="button" class="list-go-btn" onclick={() => removeGroupMember(group.id, memberId)}>Remove</button>
															</li>
														{/each}
													</ul>
												{:else}
													No members assigned.
												{/if}
											</td>
											<td>
												<div class="course-group-add-row">
													<input
														class="text-input"
														type="number"
														min="1"
														value={pendingGroupKeyLimitById[group.id] ?? group.keyLimit}
														onchange={(event) => {
															const target = event.currentTarget as HTMLInputElement;
															pendingGroupKeyLimitById = {
																...pendingGroupKeyLimitById,
																[group.id]: Math.max(1, Number(target.value) || 1)
															};
														}}
													/>
													<button type="button" class="list-go-btn" onclick={() => saveGroupKeyLimit(group.id)}>Save</button>
												</div>
											</td>
											<td>
												<div class="course-group-add-row">
													<select
														class="text-input"
														value={pendingGroupMemberIdByGroupId[group.id] || ''}
														onchange={(event) => {
															const target = event.currentTarget as HTMLSelectElement;
															pendingGroupMemberIdByGroupId = {
																...pendingGroupMemberIdByGroupId,
																[group.id]: target.value
															};
														}}
													>
														<option value="">Select course member</option>
														{#each getAvailableMembersForGroup(group) as member}
															<option value={member.id}>{member.name} ({member.id})</option>
														{/each}
													</select>
													<button type="button" class="list-go-btn" onclick={() => addGroupMember(group.id)}>Add</button>
												</div>
											</td>
										</tr>
									{/each}
								{:else}
									<tr>
										<td colspan="4">No groups found for this course yet.</td>
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

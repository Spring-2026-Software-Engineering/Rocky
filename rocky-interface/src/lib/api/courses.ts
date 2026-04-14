import { normalizeCourse, type ApiCourse, type Course } from '$lib/types/course';
import { showErrorFeedback, showSuccessFeedback } from '$lib/stores/feedbackStore';

const USER_SAFE_ACTION_FAILURE = 'Action failed. Please try again.';
const USER_SAFE_NETWORK_FAILURE = 'Unable to reach the server. Please try again.';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
	let response: Response;
	try {
		response = await fetch(url, init);
	} catch (err) {
		console.error('[courses api] network request failed', { url, err });
		throw new Error(USER_SAFE_NETWORK_FAILURE);
	}

	if (!response.ok) {
		const body = await response.text();
		console.error('[courses api] request failed', { url, status: response.status, raw: body });
		throw new Error(USER_SAFE_ACTION_FAILURE);
	}

	return (await response.json()) as T;
}

function jsonHeaders(): HeadersInit {
	return {
		'Content-Type': 'application/json',
		Accept: 'application/json'
	};
}

function getErrorMessage(err: unknown, fallback: string): string {
	return err instanceof Error && err.message.trim() ? err.message : fallback;
}

function serializeSemester(value: string): string | null {
	const normalized = value.trim().toLowerCase();
	if (!normalized || normalized === 'none') {
		return null;
	}
	return value.trim();
}

export type CreateCourseInput = {
	name: string;
	code: string;
	semester: string;
	color: string;
	instructorId: string;
	instructorName?: string;
};

export type UpdateCourseMetadataInput = {
	name: string;
	code: string;
	semester: string;
	color: string;
	instructorId: string;
};

export type CourseMemberInput = {
	id?: string;
	email?: string;
	accountEmail?: string;
	role?: 'student' | 'instructor';
};

export type ApiCourseHistoryEntry = Partial<{
	u_id: string;
	c_id: string;
	course_id: number;
	event_type: string;
	group_id: string | null;
	group_name: string | null;
	is_group_member: boolean;
	meta: Record<string, unknown>;
	created: string;
}>;

export type CourseApiHistoryEntry = {
	userId: string;
	courseCode: string;
	courseId: number;
	eventType: string;
	groupId: string | null;
	groupName: string | null;
	isGroupMember: boolean;
	meta: Record<string, unknown>;
	created: string;
};

export type RegenerateCourseApiKeyResponse = Partial<{
	api_key: string;
	owner_type: 'person' | 'group';
	owner_id: string;
	group_created_by: string | null;
	key_name: string;
	course_id: number;
	created: string;
}>;

export type CourseApiKeySummaryResponse = Partial<{
	owner_type: 'person' | 'group';
	owner_id: string;
	key_name: string;
	created: string;
	course_id: number;
}>;

export type RegenerateCourseApiKeyInput = {
	ownerType?: 'person' | 'group';
	ownerId?: string;
	groupId?: string;
	keyName?: string;
};

export async function createCourse(input: CreateCourseInput): Promise<Course> {
	try {
		const payload = {
			name: input.name.trim(),
			code: input.code.trim(),
			semester: serializeSemester(input.semester),
			color: input.color.trim(),
			instructor: input.instructorName?.trim() || '',
			instructor_ids: input.instructorId ? [input.instructorId.trim()] : [],
			student_ids: [],
			members: input.instructorId
				? [
						{
							id: input.instructorId.trim(),
							role: 'instructor'
						}
					]
				: [],
			groups: []
		};

		const rawCourse = await fetchJson<ApiCourse>('/api/backend/courses', {
			method: 'POST',
			headers: jsonHeaders(),
			body: JSON.stringify(payload)
		});

		showSuccessFeedback('Course created successfully.');
		return normalizeCourse(rawCourse);
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to create course.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function updateCourseMetadata(courseId: string | number, input: UpdateCourseMetadataInput): Promise<Course> {
	try {
		const rawCourse = await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/metadata`, {
			method: 'PATCH',
			headers: jsonHeaders(),
			body: JSON.stringify({
				name: input.name.trim(),
				code: input.code.trim(),
				semester: serializeSemester(input.semester),
				color: input.color.trim(),
				instructorId: input.instructorId.trim()
			})
		});

		showSuccessFeedback('Course updated successfully.');
		return normalizeCourse(rawCourse);
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to update course.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function addCourseMembers(courseId: string | number, members: CourseMemberInput[]): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/members`, {
			method: 'POST',
			headers: jsonHeaders(),
			body: JSON.stringify({ members })
		});

		showSuccessFeedback('Course members updated successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to add course members.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function removeCourseMember(courseId: string | number, id: string): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/members`, {
			method: 'DELETE',
			headers: jsonHeaders(),
			body: JSON.stringify({ id })
		});

		showSuccessFeedback('Course member removed successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to remove course member.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function createCourseGroup(courseId: string | number, name: string): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups`, {
			method: 'POST',
			headers: jsonHeaders(),
			body: JSON.stringify({ name })
		});

		showSuccessFeedback('Group created successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to create group.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function addGroupMember(courseId: string | number, groupId: string, id: string): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups/${groupId}/members`, {
			method: 'POST',
			headers: jsonHeaders(),
			body: JSON.stringify({ id })
		});

		showSuccessFeedback('Group member added successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to add group member.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function removeGroupMember(courseId: string | number, groupId: string, id: string): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups/${groupId}/members`, {
			method: 'DELETE',
			headers: jsonHeaders(),
			body: JSON.stringify({ id })
		});

		showSuccessFeedback('Group member removed successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to remove group member.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function regenerateCourseApiKey(
	courseId: string | number,
	input: RegenerateCourseApiKeyInput = {}
): Promise<RegenerateCourseApiKeyResponse> {
	try {
		const response = await fetchJson<RegenerateCourseApiKeyResponse>(`/api/backend/courses/${courseId}/api-key/regenerate`, {
			method: 'POST',
			headers: jsonHeaders(),
			body: JSON.stringify(input)
		});

		showSuccessFeedback('API key generated successfully.');
		return response;
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to generate API key.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function deleteCourseApiKey(courseId: string | number): Promise<void> {
	try {
		await fetchJson(`/api/backend/courses/${courseId}/api-key`, {
			method: 'DELETE',
			headers: jsonHeaders()
		});

		showSuccessFeedback('API key deleted successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to delete API key.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function fetchCourseApiHistory(courseId: string | number): Promise<CourseApiHistoryEntry[]> {
	const rawHistory = await fetchJson<ApiCourseHistoryEntry[]>(`/api/backend/courses/${courseId}/api-history`);
	return rawHistory.map((entry) => ({
		userId: entry.u_id?.trim() || 'unknown',
		courseCode: entry.c_id?.trim() || 'Unknown Course',
		courseId: typeof entry.course_id === 'number' && Number.isFinite(entry.course_id) ? entry.course_id : Number(courseId),
		eventType: entry.event_type?.trim() || 'request',
		groupId: entry.group_id?.trim() || null,
		groupName: entry.group_name?.trim() || null,
		isGroupMember: Boolean(entry.is_group_member),
		meta: entry.meta && typeof entry.meta === 'object' ? entry.meta : {},
		created: entry.created?.trim() || ''
	}));
}

export async function fetchCourseApiKeys(courseId: string | number): Promise<CourseApiKeySummaryResponse[]> {
	return fetchJson<CourseApiKeySummaryResponse[]>(`/api/backend/courses/${courseId}/api-keys`);
}

export async function updateCourseMemberKeyLimit(courseId: string | number, memberId: string, keyLimit: number): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/members/${memberId}/key-limit`, {
			method: 'PATCH',
			headers: jsonHeaders(),
			body: JSON.stringify({ keyLimit })
		});

		showSuccessFeedback('Member key limit updated successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to update member key limit.');
		showErrorFeedback(message);
		throw err;
	}
}

export async function updateCourseGroupKeyLimit(courseId: string | number, groupId: string, keyLimit: number): Promise<void> {
	try {
		await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups/${groupId}/key-limit`, {
			method: 'PATCH',
			headers: jsonHeaders(),
			body: JSON.stringify({ keyLimit })
		});

		showSuccessFeedback('Group key limit updated successfully.');
	} catch (err) {
		const message = getErrorMessage(err, 'Unable to update group key limit.');
		showErrorFeedback(message);
		throw err;
	}
}

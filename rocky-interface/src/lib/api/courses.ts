import { normalizeCourse, type ApiCourse, type Course } from '$lib/types/course';

async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
	let response: Response;
	try {
		response = await fetch(url, init);
	} catch (err) {
		const reason = err instanceof Error ? err.message : 'Unknown network error';
		throw new Error(`Network request failed for ${url}. ${reason}`);
	}

	if (!response.ok) {
		const body = await response.text();
		throw new Error(body || `Request failed (${response.status}) for ${url}`);
	}

	return (await response.json()) as T;
}

function jsonHeaders(): HeadersInit {
	return {
		'Content-Type': 'application/json',
		Accept: 'application/json'
	};
}

export type CreateCourseInput = {
	name: string;
	code: string;
	semester: string;
	instructorId: string;
	instructorName?: string;
};

export type UpdateCourseMetadataInput = {
	name: string;
	code: string;
	semester: string;
	instructorId: string;
};

export type CourseMemberInput = {
	id: string;
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

export async function createCourse(input: CreateCourseInput): Promise<Course> {
	const payload = {
		name: input.name.trim(),
		code: input.code.trim(),
		semester: input.semester.trim(),
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

	return normalizeCourse(rawCourse);
}

export async function updateCourseMetadata(courseId: string | number, input: UpdateCourseMetadataInput): Promise<Course> {
	const rawCourse = await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/metadata`, {
		method: 'PATCH',
		headers: jsonHeaders(),
		body: JSON.stringify({
			name: input.name.trim(),
			code: input.code.trim(),
			semester: input.semester.trim(),
			instructorId: input.instructorId.trim()
		})
	});

	return normalizeCourse(rawCourse);
}

export async function addCourseMembers(courseId: string | number, members: CourseMemberInput[]): Promise<void> {
	await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/members`, {
		method: 'POST',
		headers: jsonHeaders(),
		body: JSON.stringify({ members })
	});
}

export async function removeCourseMember(courseId: string | number, id: string): Promise<void> {
	await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/members`, {
		method: 'DELETE',
		headers: jsonHeaders(),
		body: JSON.stringify({ id })
	});
}

export async function createCourseGroup(courseId: string | number, name: string): Promise<void> {
	await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups`, {
		method: 'POST',
		headers: jsonHeaders(),
		body: JSON.stringify({ name })
	});
}

export async function addGroupMember(courseId: string | number, groupId: string, id: string): Promise<void> {
	await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups/${groupId}/members`, {
		method: 'POST',
		headers: jsonHeaders(),
		body: JSON.stringify({ id })
	});
}

export async function removeGroupMember(courseId: string | number, groupId: string, id: string): Promise<void> {
	await fetchJson<ApiCourse>(`/api/backend/courses/${courseId}/groups/${groupId}/members`, {
		method: 'DELETE',
		headers: jsonHeaders(),
		body: JSON.stringify({ id })
	});
}

export async function regenerateCourseApiKey(courseId: string | number): Promise<void> {
	await fetchJson(`/api/backend/courses/${courseId}/api-key/regenerate`, {
		method: 'POST',
		headers: jsonHeaders()
	});
}

export async function deleteCourseApiKey(courseId: string | number): Promise<void> {
	await fetchJson(`/api/backend/courses/${courseId}/api-key`, {
		method: 'DELETE',
		headers: jsonHeaders()
	});
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

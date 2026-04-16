import { COURSE_EDITOR_DEFAULT_COLOR } from '$lib/config/courseEditor';

export type ApiCourse = Partial<{
	id: number;
	code: string;
	name: string;
	instructor: string;
	semester: string | null;
	color: string;
	has_api_key: boolean;
	api_key_owner_type: 'person' | 'group' | null;
	api_key_owner_id: string | null;
	api_key_group_created_by: string | null;
	api_key_created: string | null;
	overview: string;
	announcements: string[];
	members: ApiCourseMember[];
	groups: ApiCourseGroup[];
}>;

export type Course = {
	id: number;
	code: string;
	name: string;
	instructor: string;
	semester: string;
	color: string;
	hasApiKey: boolean;
	apiKeyOwnerType: 'person' | 'group' | null;
	apiKeyOwnerId: string | null;
	apiKeyGroupCreatedBy: string | null;
	apiKeyCreated: string | null;
};

export type ApiCourseMember = Partial<{
	id: string | null;
	name: string | null;
	email: string;
	role: string;
	accountEmail: string;
	key_limit: number;
}>;

export type CourseAccountRecord = {
	id: string;
	name: string;
	email: string;
	role: string;
};

export type CourseMember = {
	id: string | null;
	name: string | null;
	email: string;
	role: 'instructor' | 'student';
	keyLimit: number;
};

export type ApiCourseDetail = Partial<{
	id: number;
	overview: string;
	announcements: string[];
	members: ApiCourseMember[];
}>;

export type ApiCourseGroup = Partial<{
	id: string;
	courseId: number;
	name: string;
	memberIds: string[];
	key_limit: number;
}>;

export type CourseDetail = {
	id: number;
	overview: string;
	announcements: string[];
	members: CourseMember[];
};

export type CourseGroup = {
	id: string;
	courseId: number;
	name: string;
	memberIds: string[];
	keyLimit: number;
};

export type CourseApiKeySummary = {
	ownerType: 'person' | 'group';
	ownerId: string;
	keyName: string;
	created: string;
	courseId: number;
};

function normalizeSemester(rawSemester?: string | null): string {
	const trimmed = rawSemester?.trim() || '';
	if (!trimmed || trimmed.toLowerCase() === 'none') {
		return 'None';
	}
	if (/^(spring|summer|fall)\s+\d{4}$/i.test(trimmed)) {
		const [term, year] = trimmed.split(/\s+/);
		const capitalizedTerm = `${term.charAt(0).toUpperCase()}${term.slice(1).toLowerCase()}`;
		return `${capitalizedTerm} ${year}`;
	}
	return 'None';
}

function normalizeCourseCode(rawCode?: string | null): string {
	const trimmed = rawCode?.trim() || '';
	if (!trimmed || trimmed.toLowerCase() === 'tbd 0000' || trimmed.toLowerCase() === 'none') {
		return '';
	}
	return trimmed;
}

export function normalizeCourse(raw: ApiCourse, index = 0): Course {
	const instructor = raw.instructor?.trim() || 'Unknown Instructor';

	return {
		id: typeof raw.id === 'number' && Number.isFinite(raw.id) ? raw.id : index + 1,
		code: normalizeCourseCode(raw.code),
		name: raw.name?.trim() || 'Untitled Course',
		instructor,
		semester: normalizeSemester(raw.semester),
		color: raw.color?.trim() || COURSE_EDITOR_DEFAULT_COLOR,
		hasApiKey: Boolean(raw.has_api_key),
		apiKeyOwnerType: raw.api_key_owner_type || null,
		apiKeyOwnerId: raw.api_key_owner_id?.trim() || null,
		apiKeyGroupCreatedBy: raw.api_key_group_created_by?.trim() || null,
		apiKeyCreated: raw.api_key_created?.trim() || null
	};
}

export function normalizeCourses(rawCourses: ApiCourse[]): Course[] {
	return rawCourses.map((course, index) => normalizeCourse(course, index));
}

function normalizeMemberRole(rawRole?: string): 'instructor' | 'student' {
	return rawRole?.trim().toLowerCase() === 'instructor' ? 'instructor' : 'student';
}

function toCourseMemberRole(role: string): 'instructor' | 'student' {
	return normalizeMemberRole(role);
}

function normalizeCourseMember(raw: ApiCourseMember, accountsByEmail?: Record<string, CourseAccountRecord>): CourseMember {
	const referenceEmail = raw.accountEmail?.trim().toLowerCase() || raw.email?.trim().toLowerCase() || '';
	const matchedAccount = referenceEmail ? accountsByEmail?.[referenceEmail] : undefined;
	const email = matchedAccount?.email || raw.email?.trim() || raw.accountEmail?.trim() || 'N/A';
	const name = matchedAccount?.name || raw.name?.trim() || null;
	const role = raw.role || 'student';
	const rawId = raw.id?.trim() || '';
	const id = matchedAccount?.id || rawId || null;

	return {
		id,
		name,
		email,
		role: toCourseMemberRole(role),
		keyLimit:
			typeof raw.key_limit === 'number' && Number.isFinite(raw.key_limit) && raw.key_limit > 0
				? Math.floor(raw.key_limit)
				: 1
	};
}

export function normalizeCourseDetail(raw: ApiCourseDetail, index = 0, accountsByEmail?: Record<string, CourseAccountRecord>): CourseDetail {
	return {
		id: typeof raw.id === 'number' && Number.isFinite(raw.id) ? raw.id : index + 1,
		overview: raw.overview?.trim() || 'No course overview is available yet.',
		announcements: Array.isArray(raw.announcements)
			? raw.announcements.map((item) => item?.trim() || '').filter((item) => item.length > 0)
			: [],
		members: Array.isArray(raw.members)
			? raw.members.map((member) => normalizeCourseMember(member, accountsByEmail))
			: []
	};
}

export function normalizeCourseDetails(rawDetails: ApiCourseDetail[], accountsByEmail?: Record<string, CourseAccountRecord>): CourseDetail[] {
	return rawDetails.map((detail, index) => normalizeCourseDetail(detail, index, accountsByEmail));
}

export function normalizeCourseGroup(raw: ApiCourseGroup, index = 0): CourseGroup {
	const normalizedMemberIds = Array.isArray(raw.memberIds)
		? raw.memberIds
				.map((id) => id?.trim() || '')
				.filter((id) => id.length > 0)
		: [];

	return {
		id: raw.id?.trim() || `group-${index + 1}`,
		courseId: typeof raw.courseId === 'number' && Number.isFinite(raw.courseId) ? raw.courseId : 0,
		name: raw.name?.trim() || `Group ${index + 1}`,
		memberIds: normalizedMemberIds,
		keyLimit:
			typeof raw.key_limit === 'number' && Number.isFinite(raw.key_limit) && raw.key_limit > 0
				? Math.floor(raw.key_limit)
				: 1
	};
}

export function normalizeCourseGroups(rawGroups: ApiCourseGroup[]): CourseGroup[] {
	return rawGroups.map((group, index) => normalizeCourseGroup(group, index)).filter((group) => group.courseId > 0);
}
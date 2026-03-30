export type ApiCourse = Partial<{
	id: number;
	code: string;
	name: string;
	instructor: string;
	semester: string;
	color: string;
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
};

export type ApiCourseMember = Partial<{
	id: string;
	name: string;
	email: string;
	role: string;
	accountEmail: string;
}>;

export type CourseAccountRecord = {
	id: string;
	name: string;
	email: string;
	role: string;
};

export type CourseMember = {
	id: string;
	name: string;
	email: string;
	role: 'instructor' | 'student';
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
	memberEmails: string[];
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
	memberEmails: string[];
};

function normalizeSemester(rawSemester?: string): string {
	const trimmed = rawSemester?.trim() || '';
	if (/^(spring|summer|fall)\s+\d{4}$/i.test(trimmed)) {
		const [term, year] = trimmed.split(/\s+/);
		const capitalizedTerm = `${term.charAt(0).toUpperCase()}${term.slice(1).toLowerCase()}`;
		return `${capitalizedTerm} ${year}`;
	}
	return '';
}

export function normalizeCourse(raw: ApiCourse, index = 0): Course {
	const instructor = raw.instructor?.trim() || 'Unknown Instructor';

	return {
		id: typeof raw.id === 'number' && Number.isFinite(raw.id) ? raw.id : index + 1,
		code: raw.code?.trim() || 'TBD 0000',
		name: raw.name?.trim() || 'Untitled Course',
		instructor,
		semester: normalizeSemester(raw.semester),
		color: raw.color?.trim() || '#1a4a8a'
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

function normalizeCourseMember(raw: ApiCourseMember, index = 0, accountsByEmail?: Record<string, CourseAccountRecord>): CourseMember {
	const referenceEmail = raw.accountEmail?.trim().toLowerCase() || raw.email?.trim().toLowerCase() || '';
	const matchedAccount = referenceEmail ? accountsByEmail?.[referenceEmail] : undefined;
	const email = matchedAccount?.email || raw.email?.trim() || raw.accountEmail?.trim() || 'N/A';
	const name = matchedAccount?.name || raw.name?.trim() || 'Unknown User';
	const role = raw.role || 'student';

	return {
		id: email.toLowerCase() !== 'n/a' ? email.toLowerCase() : raw.id?.trim() || `member-${index + 1}`,
		name,
		email,
		role: toCourseMemberRole(role)
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
			? raw.members.map((member, memberIndex) => normalizeCourseMember(member, memberIndex, accountsByEmail))
			: []
	};
}

export function normalizeCourseDetails(rawDetails: ApiCourseDetail[], accountsByEmail?: Record<string, CourseAccountRecord>): CourseDetail[] {
	return rawDetails.map((detail, index) => normalizeCourseDetail(detail, index, accountsByEmail));
}

export function normalizeCourseGroup(raw: ApiCourseGroup, index = 0): CourseGroup {
	const normalizedMemberEmails = Array.isArray(raw.memberEmails)
		? raw.memberEmails
				.map((email) => email?.trim().toLowerCase() || '')
				.filter((email) => email.length > 0)
		: [];

	return {
		id: raw.id?.trim() || `group-${index + 1}`,
		courseId: typeof raw.courseId === 'number' && Number.isFinite(raw.courseId) ? raw.courseId : 0,
		name: raw.name?.trim() || `Group ${index + 1}`,
		memberEmails: normalizedMemberEmails
	};
}

export function normalizeCourseGroups(rawGroups: ApiCourseGroup[]): CourseGroup[] {
	return rawGroups.map((group, index) => normalizeCourseGroup(group, index)).filter((group) => group.courseId > 0);
}
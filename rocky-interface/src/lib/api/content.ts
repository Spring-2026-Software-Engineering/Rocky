import {
	API_BASE_URL,
	LOCAL_API_ANALYTICS_ACTIVITY_URL,
	LOCAL_API_ANALYTICS_KPIS_URL,
	LOCAL_API_COURSES_URL,
	LOCAL_API_DEFAULT_WIDGETS_URL,
	LOCAL_API_HELP_FAQ_URL,
	LOCAL_API_USERS_URL,
	USE_LOCAL_API
} from '$lib/config/env';
import {
	toActivityRow,
	toKpiMetric,
	type ActivityRow,
	type KpiMetric
} from '$lib/types/analytics';
import {
	normalizeCourseDetails,
	normalizeCourseGroups,
	normalizeCourses,
	type ApiCourse,
	type ApiCourseGroup,
	type Course,
	type CourseAccountRecord,
	type CourseDetail,
	type CourseGroup
} from '$lib/types/course';
import { normalizeFaqItems, type ApiFaqItem, type FaqItem } from '$lib/types/help';
import { normalizeUsers, type ApiUser } from '$lib/types/user';
import { toPanelWidgets, type PanelWidget } from '$lib/types/widget';

function resolveLocalUrl(url: string): string {
	const base = import.meta.env.BASE_URL || '/';
	return `${base.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}`;
}

async function fetchJson<T>(url: string): Promise<T> {
	let response: Response;
	try {
		response = await fetch(url);
	} catch (err) {
		const reason = err instanceof Error ? err.message : 'Unknown network error';
		throw new Error(`Network request failed for ${url}. PUBLIC_USE_LOCAL_API=${USE_LOCAL_API}. ${reason}`);
	}

	if (!response.ok) {
		throw new Error(`Request failed (${response.status}) for ${url}`);
	}
	return (await response.json()) as T;
}

function resolveUrl(localUrl: string, apiPath: string): string {
	return USE_LOCAL_API ? resolveLocalUrl(localUrl) : `${API_BASE_URL}${apiPath}`;
}

export async function fetchCourses(): Promise<Course[]> {
	const url = resolveUrl(LOCAL_API_COURSES_URL, '/courses');
	const rawCourses = await fetchJson<ApiCourse[]>(url);
	return normalizeCourses(rawCourses);
}

async function fetchCourseAccountsByEmail(): Promise<Record<string, CourseAccountRecord>> {
	const usersUrl = resolveUrl(LOCAL_API_USERS_URL, '/users');
	const rawUsers = await fetchJson<ApiUser[]>(usersUrl);
	const users = normalizeUsers(rawUsers);

	const accountMap: Record<string, CourseAccountRecord> = {};
	for (const user of users) {
		if (!user.email || user.email === 'N/A') {
			continue;
		}

		accountMap[user.email.toLowerCase()] = {
			id: user.email.toLowerCase(),
			name: user.name,
			email: user.email,
			role: user.role
		};
	}

	return accountMap;
}

export async function fetchCourseDetails(): Promise<CourseDetail[]> {
	const coursesUrl = resolveUrl(LOCAL_API_COURSES_URL, '/courses');
	const [rawCourses, accountsByEmail] = await Promise.all([fetchJson<ApiCourse[]>(coursesUrl), fetchCourseAccountsByEmail()]);
	const rawDetails = rawCourses.map((course) => ({
		id: course.id,
		overview: course.overview,
		announcements: course.announcements,
		members: course.members
	}));
	return normalizeCourseDetails(rawDetails, accountsByEmail);
}

export async function fetchCourseGroups(): Promise<CourseGroup[]> {
	const coursesUrl = resolveUrl(LOCAL_API_COURSES_URL, '/courses');
	const rawCourses = await fetchJson<ApiCourse[]>(coursesUrl);
	const rawGroups: ApiCourseGroup[] = rawCourses.flatMap((course) => {
		const groups = Array.isArray(course.groups) ? course.groups : [];
		return groups.map((group) => ({
			...group,
			courseId: typeof group.courseId === 'number' ? group.courseId : course.id
		}));
	});
	return normalizeCourseGroups(rawGroups);
}

export async function fetchAnalyticsKpis(): Promise<KpiMetric[]> {
	const url = resolveUrl(LOCAL_API_ANALYTICS_KPIS_URL, '/analytics/kpis');
	const rawKpis = await fetchJson<Array<Partial<KpiMetric>>>(url);
	return rawKpis.map(toKpiMetric);
}

export async function fetchAnalyticsActivity(): Promise<ActivityRow[]> {
	const url = resolveUrl(LOCAL_API_ANALYTICS_ACTIVITY_URL, '/analytics/activity');
	const rawRows = await fetchJson<Array<Partial<ActivityRow>>>(url);
	return rawRows.map(toActivityRow);
}

export async function fetchDefaultWidgets(): Promise<PanelWidget[]> {
	const url = resolveUrl(LOCAL_API_DEFAULT_WIDGETS_URL, '/widgets/default');
	const rawWidgets = await fetchJson<Array<Partial<PanelWidget>>>(url);
	return toPanelWidgets(rawWidgets);
}

export async function fetchFaqItems(): Promise<FaqItem[]> {
	const url = resolveUrl(LOCAL_API_HELP_FAQ_URL, '/help/faq');
	const rawItems = await fetchJson<ApiFaqItem[]>(url);
	return normalizeFaqItems(rawItems);
}

/**
 * Derives assigned course IDs for a user based on courses where they appear as a member.
 * Courses are the authoritative source of truth for user-course relationships.
 * @param userEmail - The user's email address (normalized to lowercase for matching)
 * @param courseDetails - The list of course details with member information to search through
 * @returns Array of course IDs where the user is a member
 */
export function getUserAssignedCourseIds(userEmail: string, courseDetails: CourseDetail[]): number[] {
	const normalizedEmail = userEmail.toLowerCase();
	return courseDetails
		.filter((course) => {
			return course.members.some((member) => member.email.toLowerCase() === normalizedEmail);
		})
		.map((course) => course.id)
		.filter((id): id is number => typeof id === 'number');
}
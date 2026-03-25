import {
	API_BASE_URL,
	LOCAL_API_ACCOUNT_PROFILE_URL,
	LOCAL_API_ANALYTICS_ACTIVITY_URL,
	LOCAL_API_ANALYTICS_KPIS_URL,
	LOCAL_API_ANALYTICS_WIDGETS_URL,
	LOCAL_API_DASHBOARD_COURSES_URL,
	LOCAL_API_DEFAULT_WIDGETS_URL,
	LOCAL_API_HELP_FAQ_URL,
	USE_LOCAL_API
} from '$lib/config/env';
import {
	toActivityRow,
	toAnalyticsWidget,
	toKpiMetric,
	type ActivityRow,
	type AnalyticsWidget,
	type KpiMetric
} from '$lib/types/analytics';
import { normalizeAccountProfile, type AccountProfile, type ApiAccountProfile } from '$lib/types/account';
import { normalizeCourses, type ApiCourse, type Course } from '$lib/types/course';
import { normalizeFaqItems, type ApiFaqItem, type FaqItem } from '$lib/types/help';
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

export async function fetchDashboardCourses(): Promise<Course[]> {
	const url = resolveUrl(LOCAL_API_DASHBOARD_COURSES_URL, '/dashboard/courses');
	const rawCourses = await fetchJson<ApiCourse[]>(url);
	return normalizeCourses(rawCourses);
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

export async function fetchAnalyticsWidgets(): Promise<AnalyticsWidget[]> {
	const url = resolveUrl(LOCAL_API_ANALYTICS_WIDGETS_URL, '/analytics/widgets');
	const rawWidgets = await fetchJson<Array<Partial<AnalyticsWidget>>>(url);
	return rawWidgets.map(toAnalyticsWidget);
}

export async function fetchAccountProfile(): Promise<AccountProfile> {
	const url = resolveUrl(LOCAL_API_ACCOUNT_PROFILE_URL, '/account/profile');
	const rawProfile = await fetchJson<ApiAccountProfile>(url);
	return normalizeAccountProfile(rawProfile);
}

export async function saveAccountProfile(profile: AccountProfile): Promise<void> {
	if (USE_LOCAL_API) {
		throw new Error('Save is disabled while PUBLIC_USE_LOCAL_API=true.');
	}

	const response = await fetch(`${API_BASE_URL}/account/profile`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(profile)
	});

	if (!response.ok) {
		throw new Error(`Failed to save account profile (${response.status}).`);
	}
}

export async function fetchFaqItems(): Promise<FaqItem[]> {
	const url = resolveUrl(LOCAL_API_HELP_FAQ_URL, '/help/faq');
	const rawItems = await fetchJson<ApiFaqItem[]>(url);
	return normalizeFaqItems(rawItems);
}
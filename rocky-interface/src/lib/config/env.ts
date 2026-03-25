import {
	PUBLIC_API_BASE_URL,
	PUBLIC_APP_ENV,
	PUBLIC_ENABLE_DBTEST,
	PUBLIC_USE_LOCAL_API
} from '$env/static/public';

const trimTrailingSlash = (value: string) => value.replace(/\/+$/, '');

function requirePublicEnv(name: string, value: string): string {
	const normalized = value.trim();
	if (!normalized) {
		throw new Error(`Missing required public environment variable: ${name}`);
	}
	return normalized;
}

function parseBooleanEnv(name: string, value: string): boolean {
	if (value === 'true') {
		return true;
	}
	if (value === 'false') {
		return false;
	}
	throw new Error(`Invalid ${name}: "${value}". Expected "true" or "false".`);
}

function parseAppEnv(value: string): 'development' | 'testing' | 'production' {
	if (value === 'development' || value === 'testing' || value === 'production') {
		return value;
	}
	throw new Error(`Invalid PUBLIC_APP_ENV: "${value}". Expected one of: development, testing, production.`);
}

function parseApiBaseUrl(value: string): string {
	let parsed: URL;
	try {
		parsed = new URL(value);
	} catch {
		throw new Error(`Invalid PUBLIC_API_BASE_URL: "${value}". Expected a valid absolute URL.`);
	}

	if (parsed.protocol !== 'http:' && parsed.protocol !== 'https:') {
		throw new Error(`Invalid PUBLIC_API_BASE_URL protocol: "${parsed.protocol}". Expected http or https.`);
	}

	return trimTrailingSlash(parsed.toString());
}

export const APP_ENV = parseAppEnv(requirePublicEnv('PUBLIC_APP_ENV', PUBLIC_APP_ENV));
export const API_BASE_URL = parseApiBaseUrl(requirePublicEnv('PUBLIC_API_BASE_URL', PUBLIC_API_BASE_URL));
export const USE_LOCAL_API = parseBooleanEnv('PUBLIC_USE_LOCAL_API', requirePublicEnv('PUBLIC_USE_LOCAL_API', PUBLIC_USE_LOCAL_API));
export const ENABLE_DBTEST = parseBooleanEnv('PUBLIC_ENABLE_DBTEST', requirePublicEnv('PUBLIC_ENABLE_DBTEST', PUBLIC_ENABLE_DBTEST));

export const LOCAL_API_USERS_URL = '/local-api/users.json';
export const LOCAL_API_DASHBOARD_COURSES_URL = '/local-api/dashboard/courses.json';
export const LOCAL_API_ANALYTICS_KPIS_URL = '/local-api/analytics/kpis.json';
export const LOCAL_API_ANALYTICS_ACTIVITY_URL = '/local-api/analytics/activity.json';
export const LOCAL_API_ANALYTICS_WIDGETS_URL = '/local-api/analytics/widgets.json';
export const LOCAL_API_DEFAULT_WIDGETS_URL = '/local-api/widgets/default.json';
export const LOCAL_API_ACCOUNT_PROFILE_URL = '/local-api/account/profile.json';
export const LOCAL_API_HELP_FAQ_URL = '/local-api/help/faq.json';

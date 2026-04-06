import { env } from '$env/dynamic/public';

const PUBLIC_APP_ENV = (env.PUBLIC_APP_ENV ?? 'production').toString();
const PUBLIC_API_BASE_URL = (env.PUBLIC_API_BASE_URL ?? 'http://localhost:5001').toString();
const PUBLIC_ENABLE_DBTEST = (env.PUBLIC_ENABLE_DBTEST ?? 'false').toString();

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
export const ENABLE_DBTEST = parseBooleanEnv('PUBLIC_ENABLE_DBTEST', requirePublicEnv('PUBLIC_ENABLE_DBTEST', PUBLIC_ENABLE_DBTEST));

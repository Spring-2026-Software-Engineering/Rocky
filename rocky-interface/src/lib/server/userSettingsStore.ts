import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { API_BASE_URL, USE_LOCAL_API } from '$lib/config/env';
import { getDefaultUserSettings, sanitizeUserSettings, type UserSettingKey, type UserSettings } from '$lib/settings/userSettings';
import type { User } from '$lib/types/user';

type UserSettingsMap = Record<string, UserSettings>;

const SETTINGS_FILE_PATH = join(process.cwd(), 'data', 'user-settings.json');

function normalizeIdentityValue(value: string | undefined): string {
	return value?.trim().toLowerCase() ?? '';
}

function toUserScope(user: User): string {
	const id = normalizeIdentityValue(user.id);
	if (id.length > 0) {
		return `id:${id}`;
	}

	const email = normalizeIdentityValue(user.email);
	if (email.length > 0) {
		return `email:${email}`;
	}

	throw new Error('Authenticated user is missing a usable identity for settings storage.');
}

async function ensureSettingsDirectory(): Promise<void> {
	await mkdir(dirname(SETTINGS_FILE_PATH), { recursive: true });
}

async function readSettingsMap(): Promise<UserSettingsMap> {
	await ensureSettingsDirectory();

	try {
		const raw = await readFile(SETTINGS_FILE_PATH, 'utf-8');
		const parsed = JSON.parse(raw) as unknown;
		if (!parsed || typeof parsed !== 'object') {
			return {};
		}

		const map: UserSettingsMap = {};
		for (const [scope, value] of Object.entries(parsed as Record<string, unknown>)) {
			map[scope] = sanitizeUserSettings(value);
		}

		return map;
	} catch (err) {
		if ((err as NodeJS.ErrnoException).code === 'ENOENT') {
			return {};
		}

		if (err instanceof SyntaxError) {
			// If local settings JSON is malformed, fail safe instead of taking down page requests.
			return {};
		}

		throw err;
	}
}

async function writeSettingsMap(settingsMap: UserSettingsMap): Promise<void> {
	await ensureSettingsDirectory();
	await writeFile(SETTINGS_FILE_PATH, JSON.stringify(settingsMap, null, 2), 'utf-8');
}

async function getLocalSettingsForUser(user: User): Promise<UserSettings> {
	const scope = toUserScope(user);
	const settingsMap = await readSettingsMap();
	return settingsMap[scope] ?? getDefaultUserSettings();
}

async function updateLocalSettingForUser<K extends UserSettingKey>(
	user: User,
	key: K,
	value: UserSettings[K]
): Promise<UserSettings> {
	const scope = toUserScope(user);
	const settingsMap = await readSettingsMap();
	const current = settingsMap[scope] ?? getDefaultUserSettings();

	settingsMap[scope] = {
		...current,
		[key]: value
	};

	await writeSettingsMap(settingsMap);
	return settingsMap[scope];
}

async function updateLocalSettingsPatchForUser(user: User, patch: Partial<UserSettings>): Promise<UserSettings> {
	const scope = toUserScope(user);
	const settingsMap = await readSettingsMap();
	const current = settingsMap[scope] ?? getDefaultUserSettings();

	settingsMap[scope] = {
		...current,
		...patch
	};

	await writeSettingsMap(settingsMap);
	return settingsMap[scope];
}

function buildRemoteIdentity(user: User): { userId: string; email: string } {
	return {
		userId: user.id,
		email: user.email
	};
}

async function parseRemoteSettingsResponse(response: Response): Promise<UserSettings> {
	if (!response.ok) {
		throw new Error(`Remote user-settings request failed (${response.status}).`);
	}

	const payload = (await response.json()) as Partial<{ settings: unknown }>;
	return sanitizeUserSettings(payload.settings);
}

async function getRemoteSettingsForUser(user: User): Promise<UserSettings> {
	const identity = buildRemoteIdentity(user);
	const query = new URLSearchParams(identity);
	const response = await fetch(`${API_BASE_URL}/user-settings?${query.toString()}`, {
		method: 'GET',
		headers: {
			Accept: 'application/json'
		}
	});

	return parseRemoteSettingsResponse(response);
}

async function updateRemoteSettingForUser<K extends UserSettingKey>(
	user: User,
	key: K,
	value: UserSettings[K]
): Promise<UserSettings> {
	const identity = buildRemoteIdentity(user);
	const response = await fetch(`${API_BASE_URL}/user-settings/${key}`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json'
		},
		body: JSON.stringify({ ...identity, value })
	});

	return parseRemoteSettingsResponse(response);
}

async function updateRemoteSettingsPatchForUser(user: User, patch: Partial<UserSettings>): Promise<UserSettings> {
	const identity = buildRemoteIdentity(user);
	const response = await fetch(`${API_BASE_URL}/user-settings`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json'
		},
		body: JSON.stringify({ ...identity, patch })
	});

	return parseRemoteSettingsResponse(response);
}

export async function getSettingsForUser(user: User): Promise<UserSettings> {
	if (USE_LOCAL_API) {
		return getLocalSettingsForUser(user);
	}

	return getRemoteSettingsForUser(user);
}

export async function updateSettingForUser<K extends UserSettingKey>(
	user: User,
	key: K,
	value: UserSettings[K]
): Promise<UserSettings> {
	if (USE_LOCAL_API) {
		return updateLocalSettingForUser(user, key, value);
	}

	return updateRemoteSettingForUser(user, key, value);
}

export async function updateSettingsPatchForUser(user: User, patch: Partial<UserSettings>): Promise<UserSettings> {
	if (USE_LOCAL_API) {
		return updateLocalSettingsPatchForUser(user, patch);
	}

	return updateRemoteSettingsPatchForUser(user, patch);
}

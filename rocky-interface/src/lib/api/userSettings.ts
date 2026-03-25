import type { UserSettingKey, UserSettings } from '$lib/settings/userSettings';

async function parseResponse<T>(response: Response, action: string): Promise<T> {
	if (!response.ok) {
		throw new Error(`${action} failed (${response.status}).`);
	}

	return (await response.json()) as T;
}

export async function fetchCurrentUserSettings(): Promise<UserSettings> {
	const response = await fetch('/api/user-settings', {
		method: 'GET',
		headers: {
			Accept: 'application/json'
		}
	});

	const payload = await parseResponse<{ settings: UserSettings }>(response, 'Fetch user settings');
	return payload.settings;
}

export async function updateCurrentUserSetting<K extends UserSettingKey>(
	key: K,
	value: UserSettings[K]
): Promise<UserSettings> {
	const response = await fetch(`/api/user-settings/${key}`, {
		method: 'PATCH',
		headers: {
			'Content-Type': 'application/json',
			Accept: 'application/json'
		},
		body: JSON.stringify({ value })
	});

	const payload = await parseResponse<{ settings: UserSettings }>(response, `Update user setting "${key}"`);
	return payload.settings;
}

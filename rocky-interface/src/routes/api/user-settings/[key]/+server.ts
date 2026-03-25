import { error, json, type RequestHandler } from '@sveltejs/kit';
import { isUserSettingKey, settingsDefinitions } from '$lib/settings/userSettings';
import { updateSettingForUser } from '$lib/server/userSettingsStore';

export const PATCH: RequestHandler = async ({ locals, params, request }) => {
	if (!locals.currentUser) {
		throw error(401, 'Not authenticated.');
	}

	const settingKey = params.key;
	if (!isUserSettingKey(settingKey)) {
		throw error(400, `Unknown setting key: ${settingKey}`);
	}

	const body = (await request.json()) as Partial<{ value: unknown }>;
	const value = body.value;

	if (!settingsDefinitions[settingKey].validate(value)) {
		throw error(400, `Invalid value for setting: ${settingKey}`);
	}

	const settings = await updateSettingForUser(locals.currentUser, settingKey, value);
	return json({ ok: true, settings });
};

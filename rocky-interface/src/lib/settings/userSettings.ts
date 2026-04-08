export type ThemePreference = 'light' | 'dark';

export type UserSettings = {
	themePreference: ThemePreference;
};

export type UserSettingKey = keyof UserSettings;

type SettingDefinition<K extends UserSettingKey> = {
	defaultValue: UserSettings[K];
	validate: (value: unknown) => value is UserSettings[K];
};

export const settingsDefinitions: { [K in UserSettingKey]: SettingDefinition<K> } = {
	themePreference: {
		defaultValue: 'light',
		validate: (value): value is ThemePreference => value === 'light' || value === 'dark'
	}
};

export function isUserSettingKey(value: string): value is UserSettingKey {
	return value in settingsDefinitions;
}

export function getDefaultUserSettings(): UserSettings {
	return {
		themePreference: settingsDefinitions.themePreference.defaultValue
	};
}

export function sanitizeUserSettings(raw: unknown): UserSettings {
	const defaults = getDefaultUserSettings();
	if (!raw || typeof raw !== 'object') {
		return defaults;
	}

	const input = raw as Partial<Record<UserSettingKey, unknown>>;
	const output: UserSettings = { ...defaults };

	for (const key of Object.keys(settingsDefinitions) as UserSettingKey[]) {
		const definition = settingsDefinitions[key];
		const candidate = input[key];
		if (definition.validate(candidate)) {
			output[key] = candidate;
		}
	}

	return output;
}

export function sanitizeUserSettingsPatch(raw: unknown): Partial<UserSettings> {
	if (!raw || typeof raw !== 'object') {
		return {};
	}

	const input = raw as Partial<Record<UserSettingKey, unknown>>;
	const output: Partial<UserSettings> = {};

	for (const key of Object.keys(settingsDefinitions) as UserSettingKey[]) {
		const candidate = input[key];
		const definition = settingsDefinitions[key];
		if (definition.validate(candidate)) {
			output[key] = candidate;
		}
	}

	return output;
}

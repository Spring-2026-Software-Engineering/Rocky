import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async ({ locals }) => {
	return {
		currentUser: locals.currentUser,
		themePreference: locals.themePreference,
		userSettings: locals.userSettings,
		initialFrame: locals.initialFrame
	};
};

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		interface Locals {
			currentUser: import('$lib/types/user').User | null;
				themePreference: import('$lib/settings/userSettings').ThemePreference;
		}
		interface PageData {
			currentUser: import('$lib/types/user').User | null;
				themePreference: import('$lib/settings/userSettings').ThemePreference;
		}
		// interface PageState {}
		// interface Platform {}
	}
}

export {};

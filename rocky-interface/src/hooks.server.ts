import { redirect, type Handle } from '@sveltejs/kit';
import { getUserByEmail, SESSION_COOKIE_NAME, SESSION_COOKIE_OPTIONS } from '$lib/server/mockAuth';
import { getSettingsForUser } from '$lib/server/userSettingsStore';

const MUTATING_METHODS = new Set(['POST', 'PUT', 'PATCH', 'DELETE']);

function isRootActionRequest(pathname: string, method: string): boolean {
	return pathname === '/' && MUTATING_METHODS.has(method.toUpperCase());
}

// TODO(OAuth): Replace this mock cookie check with real OAuth session validation.
// The route-gating shape should remain the same: set event.locals.currentUser and redirect unauthenticated users.
export const handle: Handle = async ({ event, resolve }) => {
	const sessionEmail = event.cookies.get(SESSION_COOKIE_NAME);
	let currentUser = null;

	if (sessionEmail) {
		currentUser = await getUserByEmail(sessionEmail);
		if (!currentUser) {
			event.cookies.delete(SESSION_COOKIE_NAME, SESSION_COOKIE_OPTIONS);
		}
	}

	event.locals.currentUser = currentUser;
	event.locals.themePreference = 'system';

	if (currentUser) {
		const settings = await getSettingsForUser(currentUser);
		event.locals.themePreference = settings.themePreference;
	}

	const isRootPath = event.url.pathname === '/';
	const isRootAction = isRootActionRequest(event.url.pathname, event.request.method);

	if ((isRootPath || isRootAction) && !currentUser) {
		throw redirect(303, '/login');
	}

	if (event.url.pathname.startsWith('/login') && currentUser) {
		throw redirect(303, '/');
	}

	return resolve(event, {
		transformPageChunk: ({ html }) => html.replace('<html lang="en">', `<html lang="en" data-theme="${event.locals.themePreference}">`)
	});
};
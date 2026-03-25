import { redirect } from '@sveltejs/kit';
import { SESSION_COOKIE_NAME, SESSION_COOKIE_OPTIONS } from '$lib/server/mockAuth';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async ({ cookies }) => {
	cookies.delete(SESSION_COOKIE_NAME, SESSION_COOKIE_OPTIONS);
	throw redirect(303, '/login');
};

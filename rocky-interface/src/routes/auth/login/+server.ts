import { error, json, type RequestHandler } from '@sveltejs/kit';
import { getUserByEmail, SESSION_COOKIE_NAME, SESSION_COOKIE_OPTIONS } from '$lib/server/mockAuth';
import { ENABLE_PREVIEW_AUTH } from '$lib/config/env';

// TODO(OAuth): Replace this endpoint with OAuth callback/session issuance logic.
export const POST: RequestHandler = async ({ request, cookies }) => {
	if (!ENABLE_PREVIEW_AUTH) {
		throw error(404, 'Not found.');
	}

	const body = (await request.json()) as Partial<{ email: string }>;
	const email = body.email?.trim();

	if (!email) {
		throw error(400, 'Email is required.');
	}

	const user = await getUserByEmail(email);
	if (!user) {
		throw error(401, 'Invalid login user.');
	}

	cookies.set(SESSION_COOKIE_NAME, user.email, SESSION_COOKIE_OPTIONS);
	return json({ ok: true, user });
};
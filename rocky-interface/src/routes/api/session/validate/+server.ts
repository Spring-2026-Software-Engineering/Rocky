import { error, json, type RequestHandler } from '@sveltejs/kit';

export const GET: RequestHandler = async ({ locals }) => {
	if (!locals.currentUser) {
		throw error(401, 'Session expired.');
	}

	return json({ ok: true });
};

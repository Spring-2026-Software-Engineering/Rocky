import { redirect } from '@sveltejs/kit';
import { ENABLE_PREVIEW_AUTH } from '$lib/config/env';
import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async () => {
	if (!ENABLE_PREVIEW_AUTH) {
		throw redirect(303, '/login');
	}

	return {};
};

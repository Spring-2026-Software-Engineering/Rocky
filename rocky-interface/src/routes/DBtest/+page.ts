import { error } from '@sveltejs/kit';
import { ENABLE_DBTEST } from '$lib/config/env';

export const prerender = false;

export function load() {
	if (!ENABLE_DBTEST) {
		throw error(404, 'Not found');
	}
}

import { API_BASE_URL, APP_ENV } from '$lib/config/env';
import { normalizeUsers, type ApiUser, type User } from '$lib/types/user';

export const SESSION_COOKIE_NAME = 'rocky_session';

export const SESSION_COOKIE_OPTIONS = {
	path: '/',
	httpOnly: true,
	sameSite: 'lax' as const,
	secure: APP_ENV === 'production',
	maxAge: 60 * 60 * 8
};

async function loadMockUsers(): Promise<User[]> {
	const response = await fetch(`${API_BASE_URL}/auth/preview-users`, {
		method: 'GET',
		headers: {
			Accept: 'application/json'
		},
		cache: 'no-store'
	});

	if (!response.ok) {
		return [];
	}

	const parsed = (await response.json()) as ApiUser[];
	return normalizeUsers(parsed);
}

export async function getUserByEmail(email: string): Promise<User | null> {
	const users = await loadMockUsers();
	return users.find((user) => user.email.toLowerCase() === email.toLowerCase()) ?? null;
}
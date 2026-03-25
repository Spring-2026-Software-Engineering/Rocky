import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { normalizeUsers, type ApiUser, type User } from '$lib/types/user';

export const SESSION_COOKIE_NAME = 'rocky_session';

export const SESSION_COOKIE_OPTIONS = {
	path: '/',
	httpOnly: true,
	sameSite: 'lax' as const,
	secure: false,
	maxAge: 60 * 60 * 8
};

async function loadMockUsers(): Promise<User[]> {
	const filePath = join(process.cwd(), 'static', 'local-api', 'users.json');
	const raw = await readFile(filePath, 'utf-8');
	const parsed = JSON.parse(raw) as ApiUser[];
	return normalizeUsers(parsed);
}

export async function getUserByEmail(email: string): Promise<User | null> {
	const users = await loadMockUsers();
	return users.find((user) => user.email.toLowerCase() === email.toLowerCase()) ?? null;
}
import { normalizeDbUsers, normalizeUsers, type ApiUser, type DbUser, type User, type CreateUserInput, toCreateUserPayload } from '$lib/types/user';

async function fetchJson<T>(url: string): Promise<T> {
	let response: Response;
	try {
		response = await fetch(url);
	} catch (err) {
		const reason = err instanceof Error ? err.message : 'Unknown network error';
		throw new Error(`Network request failed for ${url}. ${reason}`);
	}

	if (!response.ok) {
		throw new Error(`Request failed (${response.status}) for ${url}`);
	}
	return (await response.json()) as T;
}

export async function fetchUsersForViews(): Promise<User[]> {
	const url = '/api/backend/users';
	const rawUsers = await fetchJson<ApiUser[]>(url);
	return normalizeUsers(rawUsers);
}

export async function fetchUsersForDbTest(): Promise<DbUser[]> {
	const url = '/api/backend/users';
	const rawUsers = await fetchJson<ApiUser[]>(url);
	return normalizeDbUsers(rawUsers);
}

export async function createUser(input: CreateUserInput): Promise<void> {
	const response = await fetch('/api/backend/users', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(toCreateUserPayload(input))
	});

	if (!response.ok) {
		throw new Error(`Failed to create user (${response.status}).`);
	}
}

export async function removeUser(id: string): Promise<void> {
	const response = await fetch(`/api/backend/users/${id}`, {
		method: 'DELETE'
	});

	if (!response.ok) {
		throw new Error(`Failed to delete user (${response.status}).`);
	}
}

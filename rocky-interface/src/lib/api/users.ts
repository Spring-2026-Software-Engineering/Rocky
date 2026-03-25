import { API_BASE_URL, LOCAL_API_USERS_URL, USE_LOCAL_API } from '$lib/config/env';
import { normalizeDbUsers, normalizeUsers, type ApiUser, type DbUser, type User, type CreateUserInput, toCreateUserPayload } from '$lib/types/user';

function resolveLocalUrl(url: string): string {
	const base = import.meta.env.BASE_URL || '/';
	return `${base.replace(/\/+$/, '')}/${url.replace(/^\/+/, '')}`;
}

async function fetchJson<T>(url: string): Promise<T> {
	let response: Response;
	try {
		response = await fetch(url);
	} catch (err) {
		const reason = err instanceof Error ? err.message : 'Unknown network error';
		throw new Error(`Network request failed for ${url}. PUBLIC_USE_LOCAL_API=${USE_LOCAL_API}. ${reason}`);
	}

	if (!response.ok) {
		throw new Error(`Request failed (${response.status}) for ${url}`);
	}
	return (await response.json()) as T;
}

export async function fetchUsersForViews(): Promise<User[]> {
	const url = USE_LOCAL_API ? resolveLocalUrl(LOCAL_API_USERS_URL) : `${API_BASE_URL}/users`;
	const rawUsers = await fetchJson<ApiUser[]>(url);
	return normalizeUsers(rawUsers);
}

export async function fetchUsersForDbTest(): Promise<DbUser[]> {
	const url = USE_LOCAL_API ? resolveLocalUrl(LOCAL_API_USERS_URL) : `${API_BASE_URL}/users`;
	const rawUsers = await fetchJson<ApiUser[]>(url);
	return normalizeDbUsers(rawUsers);
}

export async function createUser(input: CreateUserInput): Promise<void> {
	if (USE_LOCAL_API) {
		throw new Error('Create is disabled while PUBLIC_USE_LOCAL_API=true.');
	}

	const response = await fetch(`${API_BASE_URL}/users`, {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(toCreateUserPayload(input))
	});

	if (!response.ok) {
		throw new Error(`Failed to create user (${response.status}).`);
	}
}

export async function removeUser(id: string): Promise<void> {
	if (USE_LOCAL_API) {
		throw new Error('Delete is disabled while PUBLIC_USE_LOCAL_API=true.');
	}

	const response = await fetch(`${API_BASE_URL}/users/${id}`, {
		method: 'DELETE'
	});

	if (!response.ok) {
		throw new Error(`Failed to delete user (${response.status}).`);
	}
}

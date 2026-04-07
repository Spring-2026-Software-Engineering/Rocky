import { normalizeDbUsers, normalizeUsers, type ApiUser, type DbUser, type User, type CreateUserInput, toCreateUserPayload } from '$lib/types/user';

export type ApiWhitelistEntry = Partial<{
	first_name: string;
	last_name: string;
	email: string;
	id: string;
	is_admin: boolean;
	is_active: boolean;
	created_at: string;
}>;

export type WhitelistEntry = {
	id: string;
	firstName: string;
	lastName: string;
	displayName: string;
	email: string;
	isAdmin: boolean;
	isActive: boolean;
	createdAt: string;
};

export type CreateWhitelistEntryInput = {
	firstName: string;
	lastName: string;
	email: string;
};

function normalizeWhitelistEntry(raw: ApiWhitelistEntry): WhitelistEntry {
	const firstName = raw.first_name?.trim() || '';
	const lastName = raw.last_name?.trim() || '';
	const displayName = `${firstName} ${lastName}`.trim() || 'N/A';
	const id = raw.id?.trim() || '';

	return {
		id,
		firstName,
		lastName,
		displayName,
		email: raw.email?.trim() || 'N/A',
		isAdmin: Boolean(raw.is_admin),
		isActive: raw.is_active === undefined ? true : Boolean(raw.is_active),
		createdAt: raw.created_at?.trim() || ''
	};
}

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

export async function setUserActive(id: string, isActive: boolean): Promise<void> {
	const response = await fetch(`/api/backend/users/${id}`, {
		method: 'PUT',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ is_active: isActive })
	});

	if (!response.ok) {
		const payload = (await response.json().catch(() => ({ error: '' }))) as { error?: string };
		throw new Error(payload.error || `Failed to update user status (${response.status}).`);
	}
}

export async function fetchOAuthWhitelistEntries(): Promise<WhitelistEntry[]> {
	const url = '/api/backend/auth/microsoft/whitelist';
	const rawEntries = await fetchJson<ApiWhitelistEntry[]>(url);
	return rawEntries.map(normalizeWhitelistEntry).filter((entry) => entry.id.length > 0);
}

export async function createOAuthWhitelistEntry(input: CreateWhitelistEntryInput): Promise<void> {
	const response = await fetch('/api/backend/auth/microsoft/whitelist', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({
			firstName: input.firstName.trim(),
			lastName: input.lastName.trim(),
			email: input.email.trim()
		})
	});

	if (!response.ok) {
		const payload = (await response.json().catch(() => ({ error: '' }))) as { error?: string };
		throw new Error(payload.error || `Failed to add whitelist entry (${response.status}).`);
	}
}

export async function setWhitelistUserActive(id: string, isActive: boolean): Promise<void> {
	const response = await fetch(`/api/backend/auth/microsoft/whitelist/${id}`, {
		method: 'PATCH',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ is_active: isActive })
	});

	if (!response.ok) {
		const payload = (await response.json().catch(() => ({ error: '' }))) as { error?: string };
		throw new Error(payload.error || `Failed to update whitelist user status (${response.status}).`);
	}
}

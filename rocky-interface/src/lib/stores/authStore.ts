import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import type { User } from '$lib/types/user';

const AUTH_STORAGE_KEY = 'rocky.currentUser';

export const currentUser = writable<User | null>(null);

export function initAuthFromStorage(): void {
	if (!browser) {
		return;
	}

	const raw = localStorage.getItem(AUTH_STORAGE_KEY);
	if (!raw) {
		return;
	}

	try {
		const parsed = JSON.parse(raw) as Partial<User>;
		if (parsed.id && parsed.name && parsed.email && parsed.role) {
			currentUser.set({
				id: parsed.id,
				name: parsed.name,
				email: parsed.email,
				role: parsed.role,
				assignedCourseIds: Array.isArray(parsed.assignedCourseIds)
					? parsed.assignedCourseIds.filter((value): value is number => typeof value === 'number' && Number.isFinite(value))
					: []
			});
		}
	} catch {
		localStorage.removeItem(AUTH_STORAGE_KEY);
	}
}

export function loginAsUser(user: User): void {
	currentUser.set(user);
	if (browser) {
		localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify(user));
	}
}

export function logoutUser(): void {
	currentUser.set(null);
	if (browser) {
		localStorage.removeItem(AUTH_STORAGE_KEY);
	}
}
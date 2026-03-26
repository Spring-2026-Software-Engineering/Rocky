import { browser } from '$app/environment';
import { writable } from 'svelte/store';

const SELECTED_COURSE_KEY = 'rocky_selected_course';
const COURSE_CACHE_TTL_MS = 60 * 60 * 1000;

type CachedCourseSelection = {
	courseId: number;
	expiresAt: number;
};

function loadInitialSelectedCourseId(): number | null {
	if (!browser) {
		return null;
	}

	try {
		const raw = localStorage.getItem(SELECTED_COURSE_KEY);
		if (!raw) {
			return null;
		}

		const parsed = JSON.parse(raw) as Partial<CachedCourseSelection>;
		if (typeof parsed.courseId !== 'number' || typeof parsed.expiresAt !== 'number') {
			localStorage.removeItem(SELECTED_COURSE_KEY);
			return null;
		}

		if (Date.now() > parsed.expiresAt) {
			localStorage.removeItem(SELECTED_COURSE_KEY);
			return null;
		}

		return parsed.courseId;
	} catch {
		localStorage.removeItem(SELECTED_COURSE_KEY);
		return null;
	}
}

export const selectedCourseId = writable<number | null>(loadInitialSelectedCourseId());

if (browser) {
	selectedCourseId.subscribe((courseId) => {
		if (courseId === null) {
			localStorage.removeItem(SELECTED_COURSE_KEY);
			return;
		}

		const payload: CachedCourseSelection = {
			courseId,
			expiresAt: Date.now() + COURSE_CACHE_TTL_MS
		};

		localStorage.setItem(SELECTED_COURSE_KEY, JSON.stringify(payload));
	});
}

import { writable } from 'svelte/store';
import type { Course } from '$lib/types/course';

export type CourseComposerState = {
	isOpen: boolean;
};

const DEFAULT_STATE: CourseComposerState = {
	isOpen: false
};

export const courseComposerState = writable<CourseComposerState>(DEFAULT_STATE);
export const createdCourseDraft = writable<Course | null>(null);

export function openCourseComposer(): void {
	courseComposerState.set({
		isOpen: true
	});
}

export function closeCourseComposer(): void {
	courseComposerState.set(DEFAULT_STATE);
}

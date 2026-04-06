import { writable } from 'svelte/store';

export type CourseComposerState = {
	isOpen: boolean;
};

const DEFAULT_STATE: CourseComposerState = {
	isOpen: false
};

export const courseComposerState = writable<CourseComposerState>(DEFAULT_STATE);

export function openCourseComposer(): void {
	courseComposerState.set({
		isOpen: true
	});
}

export function closeCourseComposer(): void {
	courseComposerState.set(DEFAULT_STATE);
}

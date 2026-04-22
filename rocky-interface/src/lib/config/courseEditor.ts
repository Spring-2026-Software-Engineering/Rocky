export const COURSE_EDITOR_SEMESTER_YEAR_MIN = 2000;
export const COURSE_EDITOR_SEMESTER_YEAR_MAX = 2200;
export const COURSE_EDITOR_SEMESTER_TERMS = ['none', 'summer', 'fall', 'spring'];
export const COURSE_EDITOR_DEFAULT_COLOR = '#1a4a8a';

export function randomCourseEditorColor(): string {
	const randomHex = Math.floor(Math.random() * 0xffffff).toString(16);
	return '#' + randomHex.padStart(6, '0');
}

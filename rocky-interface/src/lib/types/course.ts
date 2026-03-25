export type ApiCourse = Partial<{
	id: number;
	code: string;
	name: string;
	instructor: string;
	semester: string;
	color: string;
}>;

export type Course = {
	id: number;
	code: string;
	name: string;
	instructor: string;
	semester: string;
	color: string;
};

function normalizeSemester(rawSemester?: string): string {
	const trimmed = rawSemester?.trim() || '';
	if (/^(spring|summer|fall)\s+\d{4}$/i.test(trimmed)) {
		const [term, year] = trimmed.split(/\s+/);
		const capitalizedTerm = `${term.charAt(0).toUpperCase()}${term.slice(1).toLowerCase()}`;
		return `${capitalizedTerm} ${year}`;
	}
	return '';
}

export function normalizeCourse(raw: ApiCourse, index = 0): Course {
	const instructor = raw.instructor?.trim() || 'Unknown Instructor';

	return {
		id: typeof raw.id === 'number' && Number.isFinite(raw.id) ? raw.id : index + 1,
		code: raw.code?.trim() || 'TBD 0000',
		name: raw.name?.trim() || 'Untitled Course',
		instructor,
		semester: normalizeSemester(raw.semester),
		color: raw.color?.trim() || '#1a4a8a'
	};
}

export function normalizeCourses(rawCourses: ApiCourse[]): Course[] {
	return rawCourses.map((course, index) => normalizeCourse(course, index));
}
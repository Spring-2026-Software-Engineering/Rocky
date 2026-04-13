import { describe, expect, it } from 'vitest';

import type { CourseDetail } from '$lib/types/course';
import { getUserAssignedCourseIds } from './content';

describe('getUserAssignedCourseIds', () => {
	it('returns only courses where the user appears in members', () => {
		const courseDetails: CourseDetail[] = [
			{
				id: 1,
				overview: '',
				announcements: [],
				members: [
					{ id: 'KSUID0001', role: 'student', name: '', email: '', keyLimit: 1 },
					{ id: null, role: 'student', name: null, email: 'future.user@example.com', keyLimit: 1 }
				]
			},
			{
				id: 2,
				overview: '',
				announcements: [],
				members: [{ id: 'KSUID0003', role: 'student', name: '', email: '', keyLimit: 1 }]
			}
		];
		expect(getUserAssignedCourseIds('KSUID0001', courseDetails)).toEqual([1]);
		expect(getUserAssignedCourseIds('KSUID0003', courseDetails)).toEqual([2]);
		expect(getUserAssignedCourseIds('KSUID9999', courseDetails)).toEqual([]);
	});

	it('matches courses for email-backed members', () => {
		const courseDetails: CourseDetail[] = [
			{
				id: 1,
				overview: '',
				announcements: [],
				members: [{ id: null, role: 'student', name: null, email: 'future.user@example.com', keyLimit: 1 }]
			}
		];

		expect(getUserAssignedCourseIds('future.user@example.com', courseDetails)).toEqual([1]);
	});
});

import { afterEach, describe, expect, it, vi } from 'vitest';

import { fetchCourseApiHistory } from './courses';

afterEach(() => {
	vi.unstubAllGlobals();
});

describe('fetchCourseApiHistory', () => {
	it('maps backend history payload to frontend shape', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				ok: true,
				json: async () => [
					{
						u_id: 'KSUID0001',
						c_id: 'SE 3010',
						course_id: 1,
						event_type: 'request',
						group_id: 'group-a',
						group_name: 'Group A',
						is_group_member: true,
						meta: { path: '/v1/ask' },
						created: '2026-04-01T00:00:00Z'
					}
				]
			})
		);

		const rows = await fetchCourseApiHistory(1);
		expect(rows).toEqual([
			{
				userId: 'KSUID0001',
				courseCode: 'SE 3010',
				courseId: 1,
				eventType: 'request',
				groupId: 'group-a',
				groupName: 'Group A',
				isGroupMember: true,
				meta: { path: '/v1/ask' },
				created: '2026-04-01T00:00:00Z'
			}
		]);
	});

	it('throws when request fails', async () => {
		vi.stubGlobal(
			'fetch',
			vi.fn().mockResolvedValue({
				ok: false,
				status: 500,
				text: async () => 'boom'
			})
		);

		await expect(fetchCourseApiHistory(1)).rejects.toThrow('Action failed. Please try again.');
	});
});

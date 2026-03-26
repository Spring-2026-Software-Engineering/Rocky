export type ApiUser = Partial<{
	_id: string;
	name: string;
	email: string;
	role: string;
	flash_id: string;
	assignedCourseIds: number[];
	course_ids: number[];
}>;

export type User = {
	id: string;
	name: string;
	email: string;
	role: string;
	assignedCourseIds: number[];
};

export type DbUser = {
	id: string;
	name: string;
	email: string;
	role: string;
	assignedCourseIds: number[];
};

function normalizeAssignedCourseIds(raw: ApiUser): number[] {
	const values = raw.assignedCourseIds ?? raw.course_ids ?? [];
	if (!Array.isArray(values)) {
		return [];
	}

	return values.filter((value): value is number => typeof value === 'number' && Number.isFinite(value));
}

export type CreateUserInput = {
	name: string;
	email: string;
	role?: string;
	flashId?: string;
};

export type CreateUserPayload = {
	name: string;
	email: string;
	role: string;
	flash_id: string;
};

export function normalizeUser(raw: ApiUser): User {
	const email = raw.email?.trim() || 'N/A';
	const id = raw._id?.trim() || (email !== 'N/A' ? email.toLowerCase() : 'unknown');

	return {
		id,
		name: raw.name?.trim() || 'N/A',
		email,
		role: raw.role?.trim() || 'N/A',
		assignedCourseIds: normalizeAssignedCourseIds(raw)
	};
}

export function normalizeUsers(rawUsers: ApiUser[]): User[] {
	return rawUsers.map(normalizeUser);
}

export function normalizeDbUser(raw: ApiUser): DbUser {
	return {
		id: raw._id?.trim() || '',
		name: raw.name?.trim() || 'N/A',
		email: raw.email?.trim() || 'N/A',
		role: raw.role?.trim() || 'N/A',
		assignedCourseIds: normalizeAssignedCourseIds(raw)
	};
}

export function normalizeDbUsers(rawUsers: ApiUser[]): DbUser[] {
	return rawUsers.map(normalizeDbUser).filter((user) => user.id.length > 0);
}

export function toCreateUserPayload(input: CreateUserInput): CreateUserPayload {
	return {
		name: input.name.trim(),
		email: input.email.trim(),
		role: input.role?.trim() || 'student',
		flash_id: input.flashId?.trim() || 'test123'
	};
}

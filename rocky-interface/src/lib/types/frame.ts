export type FrameName = 'dashboard' | 'users' | 'courses' | 'analytics' | 'account' | 'help';

const frameLabels: Record<FrameName, string> = {
	dashboard: 'Dashboard',
	users: 'Users',
	courses: 'Courses',
	analytics: 'Analytics',
	account: 'Account',
	help: 'Help'
};

export const primaryFrames: FrameName[] = ['dashboard', 'users', 'courses', 'analytics', 'account'];

const adminFrames: FrameName[] = ['dashboard', 'users', 'courses', 'analytics', 'account', 'help'];
const clientFrames: FrameName[] = ['dashboard', 'courses', 'account', 'help'];

export function framesForRole(isAdmin: boolean): FrameName[] {
	return isAdmin ? adminFrames : clientFrames;
}

export function canAccessFrame(frame: FrameName, isAdmin: boolean): boolean {
	return framesForRole(isAdmin).includes(frame);
}

export function toFrameLabel(frame: FrameName): string {
	return frameLabels[frame];
}

export function toFrameName(value: string, fallback: FrameName = 'dashboard'): FrameName {
	if (value in frameLabels) {
		return value as FrameName;
	}

	return fallback;
}

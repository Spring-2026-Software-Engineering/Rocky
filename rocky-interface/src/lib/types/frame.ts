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

export function toFrameLabel(frame: FrameName): string {
	return frameLabels[frame];
}

export function toFrameName(value: string, fallback: FrameName = 'dashboard'): FrameName {
	if (value in frameLabels) {
		return value as FrameName;
	}

	return fallback;
}

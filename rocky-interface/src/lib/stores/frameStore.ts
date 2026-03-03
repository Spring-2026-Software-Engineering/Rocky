import { writable } from 'svelte/store';
import DashboardView from '$lib/components/views/DashboardView.svelte';
import UsersView from '$lib/components/views/UsersView.svelte';
import CoursesView from '$lib/components/views/CoursesView.svelte';
import AnalyticsView from '$lib/components/views/AnalyticsView.svelte';
import AccountView from '$lib/components/views/AccountView.svelte';
import HelpView from '$lib/components/views/HelpView.svelte';

export type frameName = 'dashboard' | 'users' | 'courses' | 'analytics' | 'account' | 'help';
export type FrameComponent = typeof DashboardView | typeof UsersView | typeof CoursesView | typeof AnalyticsView | typeof AccountView | typeof HelpView;
export const frameMap: Record<frameName, FrameComponent> = {
    dashboard: DashboardView,
    users: UsersView,
    courses: CoursesView,
    analytics: AnalyticsView,
    account: AccountView,
    help: HelpView
};
export const currentFrame = writable<frameName>('dashboard');

import { writable } from 'svelte/store';
import { browser } from '$app/environment';
import DashboardView from '$lib/components/views/DashboardView.svelte';
import UsersView from '$lib/components/views/UsersView.svelte';
import CoursesView from '$lib/components/views/CoursesView.svelte';
import AnalyticsView from '$lib/components/views/AnalyticsView.svelte';
import AccountView from '$lib/components/views/AccountView.svelte';
import HelpView from '$lib/components/views/HelpView.svelte';
import type { FrameName } from '$lib/types/frame';

export type FrameComponent = typeof DashboardView | typeof UsersView | typeof CoursesView | typeof AnalyticsView | typeof AccountView | typeof HelpView;
export type { FrameName };
const FRAME_CACHE_KEY = 'rocky_current_frame';
const FRAME_CACHE_TTL_MS = 60 * 60 * 1000;

export const frameMap: Record<FrameName, FrameComponent> = {
    dashboard: DashboardView,
    users: UsersView,
    courses: CoursesView,
    analytics: AnalyticsView,
    account: AccountView,
    help: HelpView
};

function isFrameName(value: unknown): value is FrameName {
    return typeof value === 'string' && value in frameMap;
}

function loadInitialFrame(): FrameName {
    if (!browser) {
        return 'dashboard';
    }

    try {
        const rawValue = localStorage.getItem(FRAME_CACHE_KEY);
        if (!rawValue) {
            return 'dashboard';
        }

        const cached = JSON.parse(rawValue) as { frame?: unknown; expiresAt?: unknown };
        if (typeof cached.expiresAt !== 'number' || Date.now() > cached.expiresAt) {
            localStorage.removeItem(FRAME_CACHE_KEY);
            return 'dashboard';
        }

        if (isFrameName(cached.frame)) {
            return cached.frame;
        }
    } catch {
        localStorage.removeItem(FRAME_CACHE_KEY);
    }

    return 'dashboard';
}

export const currentFrame = writable<FrameName>(loadInitialFrame());

if (browser) {
    currentFrame.subscribe((frame) => {
        const expiresAt = Date.now() + FRAME_CACHE_TTL_MS;
        localStorage.setItem(FRAME_CACHE_KEY, JSON.stringify({ frame, expiresAt }));
    });
}

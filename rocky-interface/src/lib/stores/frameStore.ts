import { writable } from 'svelte/store';
export type Frame = 'dashboard' | 'users' | 'courses' | 'analytics' | 'account' | 'help';
export const currentFrame = writable<Frame>('dashboard');

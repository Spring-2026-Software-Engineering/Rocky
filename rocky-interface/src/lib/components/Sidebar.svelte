	<script lang="ts">
	import '$lib/styles/sidebar.css';
	import { currentFrame, frameMap } from '$lib/stores/frameStore';
	import { toFrameLabel, type FrameName } from '$lib/types/frame';

	const frames = Object.keys(frameMap) as FrameName[];
	const primaryFrames = frames.filter((frame) => frame !== 'help');
	const SESSION_VALIDATE_TTL_MS = 10_000;
	let lastSessionValidationAt = 0;
	let sessionValidationInFlight: Promise<boolean> | null = null;

	async function validateSession(): Promise<boolean> {
		if (Date.now() - lastSessionValidationAt < SESSION_VALIDATE_TTL_MS) {
			return true;
		}

		if (sessionValidationInFlight) {
			return sessionValidationInFlight;
		}

		sessionValidationInFlight = (async () => {
			const response = await fetch('/api/session/validate', { method: 'GET', cache: 'no-store' });
			if (!response.ok) {
				return false;
			}

			lastSessionValidationAt = Date.now();
			return true;
		})();

		try {
			return await sessionValidationInFlight;
		} finally {
			sessionValidationInFlight = null;
		}
	}

	async function handleFrameChange(frame: FrameName) {
		if ($currentFrame === frame) {
			return;
		}

		try {
			const isValid = await validateSession();
			if (!isValid) {
				window.location.href = '/login';
				return;
			}

			currentFrame.set(frame);
		} catch (error) {
			console.error('Session validation error:', error);
			window.location.href = '/login';
		}
	}
</script>

<nav class="sidebar">
	{#each primaryFrames as frame}
		<button class="nav-link" class:active={$currentFrame === frame} on:click={() => handleFrameChange(frame)}>{toFrameLabel(frame)}</button>
	{/each}

	<div class="spacer"></div>

	<button class="nav-link" class:active={$currentFrame === 'help'} on:click={() => handleFrameChange('help')}>{toFrameLabel('help')}</button>
</nav>

<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import { setThemePreference } from '$lib/stores/themeStore';
	import '$lib/styles/routes/account.css';

	let isDarkMode = $state(page.data.themePreference === 'dark');
	let currentUser = $derived(page.data.currentUser);

	async function handleThemeToggle() {
		const previousValue = isDarkMode;
		isDarkMode = !previousValue;

		try {
			await setThemePreference(isDarkMode ? 'dark' : 'light');
		} catch {
			isDarkMode = previousValue;
		}
	}

	function logout() {
		void goto('/logout');
	}
</script>

<ViewShell title="Account Profile">
	<div slot="actions">
		<button class="view-btn" onclick={logout}>Log Out</button>
	</div>
	
	<section class="section account-card">
		<div class="account-profile-header">
			<div class="account-identity">
				<h2 class="account-name">
					{currentUser ? `${currentUser.firstName} ${currentUser.lastName}` : 'Unknown User'}
				</h2>
				<p><strong>ID:</strong> {currentUser?.id ?? '-'}</p>
				<p><strong>Email:</strong> {currentUser?.email ?? '-'}</p>
			</div>
		</div>

		<div class="account-divider" aria-hidden="true"></div>

		<div class="account-theme-row">
			<div>
				<p class="account-theme-title">Dark Mode</p>
				<p class="account-note">Adjust the appearance of the interface.</p>
			</div>
			<button
				type="button"
				class="account-toggle"
				class:account-toggle-active={isDarkMode}
				onclick={handleThemeToggle}
				aria-pressed={isDarkMode}
				aria-label="Toggle dark mode"
			>
				<span class="account-toggle-knob"></span>
			</button>
		</div>
	</section>
</ViewShell>

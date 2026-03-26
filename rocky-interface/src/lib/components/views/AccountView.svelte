<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import { setThemePreference } from '$lib/stores/themeStore';
	import type { ThemePreference } from '$lib/settings/userSettings';

	let selectedTheme = $state<ThemePreference>((page.data.themePreference || 'system') as ThemePreference);

	async function handleThemeChange(event: Event) {
		const value = (event.currentTarget as HTMLSelectElement).value as ThemePreference;
		selectedTheme = value;

		try {
			await setThemePreference(selectedTheme);
		} catch {
			selectedTheme = (page.data.themePreference || 'system') as ThemePreference;
		}
	}

	function logout() {
		void goto('/logout');
	}
</script>

<ViewShell title="Account Settings">
	<div slot="actions">
		<button class="view-btn" onclick={logout}>Log Out</button>
	</div>

		<section class="section">
			<div class="section-header">
				<h2>Appearance</h2>
			</div>

			<div class="section-content">
				<div class="form-group">
					<label for="themePreference" class="form-label">Theme Preference</label>
					<select id="themePreference" class="text-input" bind:value={selectedTheme} onchange={handleThemeChange}>
						<option value="light">Light</option>
						<option value="dark">Dark</option>
						<option value="system">System Default</option>
					</select>
					<p class="account-note">Changes apply immediately and are saved to your account.</p>
				</div>
			</div>
		</section>
</ViewShell>

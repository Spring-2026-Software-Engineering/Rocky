<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import { profilePictureOptions } from '$lib/settings/userSettings';
	import { setThemePreference } from '$lib/stores/themeStore';
	import { updateCurrentUserSetting } from '$lib/api/userSettings';
	import '$lib/styles/routes/modules/account-view.css';

	let isDarkMode = $state(page.data.themePreference === 'dark');
	let currentUser = $derived(page.data.currentUser);
	let savedProfilePicture = $state(page.data.userSettings.profilePicture);
	let draftProfilePicture = $state(page.data.userSettings.profilePicture);
	let isProfilePickerOpen = $state(false);

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

	function openProfilePicker() {
		draftProfilePicture = savedProfilePicture;
		isProfilePickerOpen = true;
	}

	function cancelProfilePicture() {
		draftProfilePicture = savedProfilePicture;
		isProfilePickerOpen = false;
	}

	async function saveProfilePicture() {
		const previousValue = savedProfilePicture;
		savedProfilePicture = draftProfilePicture;
		isProfilePickerOpen = false;

		try {
			const settings = await updateCurrentUserSetting('profilePicture', draftProfilePicture);
			savedProfilePicture = settings.profilePicture;
			draftProfilePicture = settings.profilePicture;
		} catch {
			savedProfilePicture = previousValue;
			draftProfilePicture = previousValue;
		}
	}
</script>

<ViewShell title="Account Profile">
	<div slot="actions">
		<button class="view-btn" onclick={logout}>Log Out</button>
	</div>
	
	<section class="section account-card">
		<div class="account-profile-header">
			<div class="account-avatar-wrap">
				<button
					type="button"
					class="account-avatar-button"
					onclick={openProfilePicker}
					aria-haspopup="dialog"
					aria-expanded={isProfilePickerOpen}
					aria-label="Choose profile picture"
				>
					<img class="account-avatar" src={savedProfilePicture} alt="" />
				</button>

				{#if isProfilePickerOpen}
					<div class="account-avatar-picker" role="dialog" aria-label="Choose profile picture">
						<div class="account-avatar-grid">
							{#each profilePictureOptions as option}
								<button
									type="button"
									class="account-avatar-option"
									class:account-avatar-option-active={draftProfilePicture === option.value}
									onclick={() => (draftProfilePicture = option.value)}
									aria-label={option.label}
									aria-pressed={draftProfilePicture === option.value}
								>
									<img src={option.value} alt="" />
								</button>
							{/each}
						</div>
						<div class="account-avatar-actions">
							<button type="button" class="account-avatar-cancel" onclick={cancelProfilePicture}>Cancel</button>
							<button type="button" class="account-avatar-save" onclick={saveProfilePicture}>Save</button>
						</div>
					</div>
				{/if}
			</div>
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

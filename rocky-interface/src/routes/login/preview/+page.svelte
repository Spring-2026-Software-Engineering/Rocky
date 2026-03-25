<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { fetchUsersForViews } from '$lib/api/users';
	import '$lib/styles/login.css';
	import type { User } from '$lib/types/user';

	let users: User[] = [];
	let isLoading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			users = await fetchUsersForViews();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unable to load users.';
		} finally {
			isLoading = false;
		}
	});

	async function enterAsUser(user: User) {
		const response = await fetch('/auth/login', {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json'
			},
			body: JSON.stringify({ email: user.email })
		});

		if (!response.ok) {
			error = 'Unable to create preview session.';
			return;
		}

		window.location.href = '/';
	}
</script>

<div class="login-background">
	<div class="login-overlay login-preview-overlay">
		<section class="preview-shell">
			<header class="preview-header">
				<h1>Login Preview</h1>
				<p>Select a local-api user to test the app without OAuth.</p>
			</header>

			{#if isLoading}
				<div class="preview-state">Loading users...</div>
			{:else if error}
				<div class="preview-state preview-error">{error}</div>
			{:else if users.length === 0}
				<div class="preview-state">No users available in local-api.</div>
			{:else}
				<div class="preview-user-grid">
					{#each users as user}
						<article class="preview-user-card">
							<h2>{user.name}</h2>
							<p>{user.email}</p>
							<span class="preview-role">{user.role}</span>
							<button class="login-signin-btn" type="button" on:click={() => enterAsUser(user)}>Continue as {user.name}</button>
						</article>
					{/each}
				</div>
			{/if}

			<a class="preview-back" href="/login">Back to Login</a>
		</section>
	</div>
</div>
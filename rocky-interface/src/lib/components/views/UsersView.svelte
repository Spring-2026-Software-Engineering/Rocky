<script lang="ts">
	import { onMount } from 'svelte';
	import { fetchUsersForViews } from '$lib/api/users';
	import type { User } from '$lib/types/user';
	import ViewShell from '$lib/components/ViewShell.svelte';

	let users: User[] = [];
	let isLoading = true;
	let error: string | null = null;

	onMount(async () => {
		try {
			users = await fetchUsersForViews();
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	});
</script>

<ViewShell title="Users" description="View and manage system users and their roles.">
		{#if isLoading}
			<div class="empty-state">
				<p>Loading users...</p>
			</div>
		{:else if error}
			<div class="empty-state">
				<p><strong>Error:</strong> {error}</p>
			</div>
		{:else if users.length === 0}
			<div class="empty-state">
				<p>No users found.</p>
			</div>
		{:else}
			<section class="section">
				<div class="table-container">
					<table class="data-table">
						<thead>
							<tr>
								<th>Name</th>
								<th>Email</th>
								<th>Role</th>
							</tr>
						</thead>
						<tbody>
							{#each users as user}
								<tr>
									<td>{user.name}</td>
									<td>{user.email}</td>
									<td>{user.role}</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			</section>
		{/if}
</ViewShell>

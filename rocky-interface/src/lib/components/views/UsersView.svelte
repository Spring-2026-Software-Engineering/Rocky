<script lang="ts">
	import { onMount } from 'svelte';
	import {
		createOAuthWhitelistEntry,
		fetchOAuthWhitelistEntries,
		fetchUsersForViews,
		setUserActive,
		setWhitelistUserActive,
		type WhitelistEntry
	} from '$lib/api/users';
	import type { User } from '$lib/types/user';
	import ViewShell from '$lib/components/ViewShell.svelte';
	import '$lib/styles/routes/users.css';

	type UserTab = 'kent' | 'whitelist';

	let users: User[] = [];
	let whitelistEntries: WhitelistEntry[] = [];
	let kentUsers: User[] = [];
	let activeWhitelistEntries: WhitelistEntry[] = [];
	let activeTab: UserTab = 'kent';
	let isLoading = true;
	let error: string | null = null;
	let whitelistError: string | null = null;
	let whitelistMessage: string | null = null;
	let isSavingWhitelist = false;
	let searchQuery = '';
	let sortByName = false;

	let firstName = '';
	let lastName = '';
	let email = '';

	onMount(async () => {
		try {
			const [loadedUsers, loadedWhitelist] = await Promise.all([fetchUsersForViews(), fetchOAuthWhitelistEntries()]);
			users = loadedUsers;
			whitelistEntries = loadedWhitelist;
		} catch (err) {
			error = err instanceof Error ? err.message : 'An error occurred';
		} finally {
			isLoading = false;
		}
	});

	$: kentUsers = users.filter((user) => user.email.toLowerCase().endsWith('@kent.edu'));
	$: activeWhitelistEntries = whitelistEntries;

	async function refreshUsers(): Promise<void> {
		users = await fetchUsersForViews();
	}

	async function refreshWhitelist(): Promise<void> {
		whitelistEntries = await fetchOAuthWhitelistEntries();
	}

	async function addWhitelistEntry(): Promise<void> {
		if (!firstName.trim() || !lastName.trim() || !email.trim()) {
			whitelistError = 'First name, last name, and email are required.';
			return;
		}

		whitelistError = null;
		whitelistMessage = null;
		isSavingWhitelist = true;

		try {
			await createOAuthWhitelistEntry({ firstName, lastName, email });
			await refreshWhitelist();
			firstName = '';
			lastName = '';
			email = '';
			whitelistMessage = 'Whitelist entry added.';
		} catch (err) {
			whitelistError = err instanceof Error ? err.message : 'Unable to add whitelist entry.';
		} finally {
			isSavingWhitelist = false;
		}
	}

	async function setWhitelistActive(id: string, isActive: boolean): Promise<void> {
		whitelistError = null;
		whitelistMessage = null;
		isSavingWhitelist = true;

		try {
			await setWhitelistUserActive(id, isActive);
			await refreshWhitelist();
			await refreshUsers();
			whitelistMessage = isActive ? 'Whitelist user activated.' : 'Whitelist user deactivated.';
		} catch (err) {
			whitelistError = err instanceof Error ? err.message : 'Unable to update whitelist user status.';
		} finally {
			isSavingWhitelist = false;
		}
	}

	async function setKentUserActive(id: string, isActive: boolean): Promise<void> {
		whitelistError = null;
		whitelistMessage = null;
		isSavingWhitelist = true;

		try {
			await setUserActive(id, isActive);
			await refreshUsers();
			whitelistMessage = isActive ? 'User activated.' : 'User deactivated.';
		} catch (err) {
			whitelistError = err instanceof Error ? err.message : 'Unable to update user status.';
		} finally {
			isSavingWhitelist = false;
		}
	}

</script>

<ViewShell title="Users">
		{#if isLoading}
			<div class="empty-state">
				<p>Loading users...</p>
			</div>
		{:else if error}
			<div class="empty-state">
				<p><strong>Error:</strong> {error}</p>
			</div>
		{:else}
		
			<section class="section">

				<div class="user-tab-bar" role="tablist" aria-label="User email categories">
					
					<input
					type="text"
					placeholder="Search users"
					bind:value={searchQuery}
					class="view-btn"
					/>

					<button type="button" class="view-btn user-tab-btn" class:user-tab-active={activeTab === 'kent'} onclick={() => (activeTab = 'kent')}>
						Kent Emails
					</button>
					<button type="button" class="view-btn user-tab-btn" class:user-tab-active={activeTab === 'whitelist'} onclick={() => (activeTab = 'whitelist')}>
						Whitelist Emails
					</button>
				</div>


				{#if activeTab === 'kent'}
					<div class="table-container">
						<table class="data-table users-table">
							<colgroup>
								<col class="users-col-name" />
								<col class="users-col-email" />
								<col class="users-col-id" />
								<col class="users-col-admin" />
								<col class="users-col-active" />
								<col class="users-col-actions" />
							</colgroup>
							<thead>
								<tr>
									<th
										style="cursor: pointer; user-select: none;"
										onclick={() => (sortByName = !sortByName)} 
									>
										Name {sortByName ? '▲' : '▼'}
									</th>
									<th>Email</th>
									<th>ID</th>
									<th>Admin</th>
									<th>Active</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{#if kentUsers.length === 0}
									<tr>
										<td colspan="6">No Kent email users found.</td>
									</tr>
								{:else}
									{#each kentUsers.filter((user) =>
										user.displayName?.toLowerCase().includes(searchQuery.toLowerCase())
									)
									.sort((a, b) =>
										sortByName
											? (a.displayName ?? '').localeCompare(b.displayName ?? '')
											: 0
									) as user}
										<tr>
											<td>{user.displayName}</td>
											<td>{user.email}</td>
											<td>{user.id}</td>
											<td>{user.isAdmin ? 'Yes' : 'No'}</td>
											<td>{user.isActive ? 'Yes' : 'No'}</td>
											<td>
												<div class="user-actions">
													<button
														class="view-btn user-action-btn"
														type="button"
														onclick={() => setKentUserActive(user.id, !user.isActive)}
														disabled={isSavingWhitelist}
													>
														{user.isActive ? 'Deactivate' : 'Activate'}
													</button>
												</div>
											</td>
										</tr>
									{/each}
								{/if}
							</tbody>
						</table>
					</div>
				{:else}
					<div class="whitelist-form">
						<input type="text" placeholder="First Name" bind:value={firstName} />
						<input type="text" placeholder="Last Name" bind:value={lastName} />
						<input type="email" placeholder="Email" bind:value={email} />
						<button class="view-btn" type="button" onclick={addWhitelistEntry} disabled={isSavingWhitelist}>Add</button>
					</div>

					{#if whitelistError}
						<p class="whitelist-feedback whitelist-error"><strong>Error:</strong> {whitelistError}</p>
					{/if}
					{#if whitelistMessage}
						<p class="whitelist-feedback">{whitelistMessage}</p>
					{/if}

					<div class="table-container">
						<table class="data-table users-table">
							<colgroup>
								<col class="users-col-name" />
								<col class="users-col-email" />
								<col class="users-col-id" />
								<col class="users-col-admin" />
								<col class="users-col-active" />
								<col class="users-col-actions" />
							</colgroup>
							<thead>
								<tr>
									<th>Name</th>
									<th>Email</th>
									<th>ID</th>
									<th>Admin</th>
									<th>Active</th>
									<th>Actions</th>
								</tr>
							</thead>
							<tbody>
								{#if activeWhitelistEntries.length === 0}
									<tr>
										<td colspan="6">No whitelist entries found.</td>
									</tr>
								{:else}
									{#each activeWhitelistEntries as entry}
										<tr>
											<td>{entry.displayName}</td>
											<td>{entry.email}</td>
											<td>{entry.id}</td>
											<td>{entry.isAdmin ? 'Yes' : 'No'}</td>
											<td>{entry.isActive ? 'Yes' : 'No'}</td>
											<td>
												<div class="user-actions">
													<button
														class="view-btn user-action-btn"
														type="button"
														onclick={() => setWhitelistActive(entry.id, !entry.isActive)}
														disabled={isSavingWhitelist}
													>
														{entry.isActive ? 'Deactivate' : 'Activate'}
													</button>
												</div>
											</td>
										</tr>
									{/each}
								{/if}
							</tbody>
						</table>
					</div>
				{/if}
			</section>
		{/if}
</ViewShell>

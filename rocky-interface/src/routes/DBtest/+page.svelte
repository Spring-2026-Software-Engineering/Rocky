<script lang="ts">
	import { createUser, fetchUsersForDbTest, removeUser } from '$lib/api/users';
	import { USE_LOCAL_API } from '$lib/config/env';
	import type { DbUser } from '$lib/types/user';

	let users: DbUser[] = [];
	let name: string = '';
	let email: string = '';
	let role: string = 'student';
	let message: string | null = null;

	async function loadUsers() {
		message = null;
		users = await fetchUsersForDbTest();
	}

	async function addUser() {
		message = null;
		try {
			await createUser({ name, email, role });
		} catch (err) {
			message = err instanceof Error ? err.message : 'Unable to add user.';
			return;
		}

		name = '';
		email = '';
		role = 'student';
		await loadUsers();
	}

	async function deleteUser(id: string) {
		message = null;
		try {
			await removeUser(id);
		} catch (err) {
			message = err instanceof Error ? err.message : 'Unable to delete user.';
			return;
		}
		await loadUsers();
	}
</script>

<h1>Database Test Page</h1>

{#if USE_LOCAL_API}
	<p>Offline local-api mode is enabled. Create/Delete operations are disabled.</p>
{/if}

{#if message}
	<p>{message}</p>
{/if}

<button on:click={loadUsers}>Display Users</button>

<h3>Add User</h3>
<input placeholder="name" bind:value={name} />
<input placeholder="email" bind:value={email} />
<input placeholder="role (student/instructor/admin)" bind:value={role} />
<button on:click={addUser} disabled={USE_LOCAL_API}>Add User</button>

<h3>Users</h3>
<ul>
	{#each users as user}
		<li>
			{user.name} ({user.email})
			<button on:click={() => deleteUser(user.id)} disabled={USE_LOCAL_API}>Delete</button>
		</li>
	{/each}
</ul>

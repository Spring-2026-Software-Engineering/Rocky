<script lang="ts">
	import { createUser, fetchUsersForDbTest, removeUser } from '$lib/api/users';
	import type { DbUser } from '$lib/types/user';

	let users: DbUser[] = [];
	let firstName: string = '';
	let lastName: string = '';
	let email: string = '';
	let isAdmin = false;
	let message: string | null = null;

	async function loadUsers() {
		message = null;
		users = await fetchUsersForDbTest();
	}

	async function addUser() {
		message = null;
		try {
			await createUser({ firstName, lastName, email, isAdmin });
		} catch (err) {
			message = err instanceof Error ? err.message : 'Unable to add user.';
			return;
		}

		firstName = '';
		lastName = '';
		email = '';
		isAdmin = false;
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

{#if message}
	<p>{message}</p>
{/if}

<button on:click={loadUsers}>Display Users</button>

<h3>Add User</h3>
<input placeholder="first name" bind:value={firstName} />
<input placeholder="last name" bind:value={lastName} />
<input placeholder="email" bind:value={email} />
<label>
	<input type="checkbox" bind:checked={isAdmin} /> Admin
</label>
<button on:click={addUser}>Add User</button>

<h3>Users</h3>
<ul>
	{#each users as user}
		<li>
			{user.displayName} ({user.email}) - {user.isAdmin ? 'Admin' : 'User'}
			<button on:click={() => deleteUser(user.id)}>Delete</button>
		</li>
	{/each}
</ul>

<script lang="ts">
type User = {
_id: string;
name: string;
email: string;
};


let users: User[] = [];
let name: string = '';
let email: string = '';


async function loadUsers() {
const res = await fetch('http://localhost:5001/users');
users = await res.json();
}


async function addUser() {
await fetch('http://localhost:5001/users', {
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
name,
email,
flash_id: "test123",
role: "student"
})
});


name = '';
email = '';
loadUsers();
}


async function deleteUser(id: string) {
await fetch(`http://localhost:5001/users/${id}`, {
method: 'DELETE'
});
loadUsers();
}
</script>


<h1>Database Test Page</h1>


<button on:click={loadUsers}>Display Users</button>


<h3>Add User</h3>
<input placeholder="name" bind:value={name} />
<input placeholder="email" bind:value={email} />
<button on:click={addUser}>Add User</button>


<h3>Users</h3>
<ul>
{#each users as user}
<li>
{user.name} ({user.email})
<button on:click={() => deleteUser(user._id)}>Delete</button>
</li>
{/each}
</ul>


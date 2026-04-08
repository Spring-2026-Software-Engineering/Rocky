<script lang="ts">
  import { onMount } from 'svelte';

  type User = {
    name: string;
    email: string;
    role: string;
  };

  let users: User[] = [];

  //sort users by role

  const roleOrder: Record<string, number> = {
    admin: 1,
    instructor: 2,
    student: 3
  };

  onMount(() => {
    async function fetchUsers() {
      const res = await fetch('http://localhost:5001/users');
      const data: User[] = await res.json();

      users = data.map(u => ({
        name: u.name || 'N/A',
        email: u.email || 'N/A',
        role: u.role || 'N/A'
      }));

      //sort
      users = [...users].sort(
      (a, b) => roleOrder[a.role.toLowerCase()] - roleOrder[b.role.toLowerCase()]
      );
    }

    fetchUsers();
  });

  
</script>

<h1>Users</h1>

{#if users.length === 0}
  <p>No users found.</p>
{:else}
  <table style="border-collapse: collapse; width: 100%;">
    <thead>
      <tr>
        <th style="border: 1px solid #ddd; padding: 8px;">Name</th>
        <th style="border: 1px solid #ddd; padding: 8px;">Email</th>
        <th style="border: 1px solid #ddd; padding: 8px;">Role</th>
      </tr>
    </thead>
    <tbody>
      {#each users as user}
        <tr>
          <td style="border: 1px solid #ddd; padding: 8px;">{user.name}</td>
          <td style="border: 1px solid #ddd; padding: 8px;">{user.email}</td>
          <td style="border: 1px solid #ddd; padding: 8px;">{user.role}</td>
        </tr>
      {/each}
    </tbody>
  </table>
{/if}
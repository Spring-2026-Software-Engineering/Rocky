<script lang="ts">
	import type { User } from '$lib/types/user';
	import '$lib/styles/components/topbar.css';

	let { user = null }: { user: User | null } = $props();

	let roleValue = $derived(user?.role?.trim().toLowerCase() ?? '');
	let showAdministration = $derived(roleValue === 'admin' || roleValue === 'administrator');
</script>

<header class="topbar">
		<img src="/rocky.svg" alt="Rocky" class="brand-logo" />
		<div class="brand-text">
			<div class="brand-name">Rocky</div>
			{#if showAdministration}
				<div class="brand-sub">administration</div>
			{/if}
		</div>
		<img src="/ksu_horizontal_white.png" alt="Kent State University" class="ksu-logo" />
</header>

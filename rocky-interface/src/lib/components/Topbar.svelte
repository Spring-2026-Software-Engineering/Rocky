<script lang="ts">
	import type { User } from '$lib/types/user';
	import '$lib/styles/components/modules/topbar.css';
	import  {sidebarOpen} from '$lib/stores/sidebarStore';

	let { user = null }: { user: User | null } = $props();

	let showAdministration = $derived(Boolean(user?.isAdmin));
	const isHamburgerDay = Math.random() < 0.05; //  x% chance to show the hamburger icon 
</script>

<header class="topbar">
		<button class="hamburger" aria-label="Toggle menu" onclick={() => sidebarOpen.update(open => !open)}>
			{#if isHamburgerDay}
				<img src="/hamburger.svg" alt="Menu" class="hamburger-icon" />
			{:else}
				<span class="hamburger-line"></span>
				<span class="hamburger-line"></span>
				<span class="hamburger-line"></span>
			{/if}
		</button>

		<img src="/rocky.svg" alt="Rocky" class="brand-logo" />
		<div class="brand-text">
			<div class="brand-name">Rocky</div>
			{#if showAdministration}
				<div class="brand-sub">administration</div>
			{/if}
		</div>
		<img src="/ksu_horizontal_white.png" alt="Kent State University" class="ksu-logo" />
</header>

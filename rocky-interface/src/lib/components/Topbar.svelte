<script lang="ts">
	import type { User } from '$lib/types/user';
	import '$lib/styles/topbar.css';

	export let user: User | null = null;

	$: roleLabel = user ? user.role : 'Administrator';
	$: nameLabel = user ? user.name : 'Rocky';
</script>

<header class="topbar">
		<img src="/rock.png" alt="Rocky" class="brand-logo" />
		<div class="brand-text">
			<div class="brand-name">{nameLabel}</div>
			<div class="brand-sub">{roleLabel}</div>
		</div>
</header>

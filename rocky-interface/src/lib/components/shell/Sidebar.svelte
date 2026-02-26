<script>
	import '$lib/styles/sidebar.css';
	import { currentFrame } from '$lib/stores/frameStore';
</script>

<nav class="sidebar">
	<button class="nav-link" class:active={$currentFrame === 'dashboard'} on:click={() => currentFrame.set('dashboard')}>Dashboard</button>
	<button class="nav-link" class:active={$currentFrame === 'users'} on:click={() => currentFrame.set('users')}>Users</button>
	<button class="nav-link" class:active={$currentFrame === 'courses'} on:click={() => currentFrame.set('courses')}>Courses</button>
	<button class="nav-link" class:active={$currentFrame === 'analytics'} on:click={() => currentFrame.set('analytics')}>Analytics</button>
	<button class="nav-link" class:active={$currentFrame === 'account'} on:click={() => currentFrame.set('account')}>Account</button>

	<div class="spacer"></div>

	<button class="nav-link" class:active={$currentFrame === 'help'} on:click={() => currentFrame.set('help')}>Help</button>
</nav>

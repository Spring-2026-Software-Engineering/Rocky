<script>
	import { currentFrame } from '$lib/stores/frameStore';

	import DashboardView from '$lib/components/views/DashboardView.svelte';
	import UsersView from '$lib/components/views/UsersView.svelte';
	import CoursesView from '$lib/components/views/CoursesView.svelte';
	import AnalyticsView from '$lib/components/views/AnalyticsView.svelte';
	import AccountView from '$lib/components/views/AccountView.svelte';
	import HelpView from '$lib/components/views/HelpView.svelte';
</script>

{#if $currentFrame === 'dashboard'}
	<DashboardView />
{:else if $currentFrame === 'users'}
	<UsersView />
{:else if $currentFrame === 'courses'}
	<CoursesView />
{:else if $currentFrame === 'analytics'}
	<AnalyticsView />
{:else if $currentFrame === 'account'}
	<AccountView />
{:else if $currentFrame === 'help'}
	<HelpView />
{/if}

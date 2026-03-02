<script lang="ts">
	import { currentFrame, type Frame } from '$lib/stores/frameStore';

	import DashboardView from '$lib/components/views/DashboardView.svelte';
	import UsersView from '$lib/components/views/UsersView.svelte';
	import CoursesView from '$lib/components/views/CoursesView.svelte';
	import AnalyticsView from '$lib/components/views/AnalyticsView.svelte';
	import AccountView from '$lib/components/views/AccountView.svelte';
	import HelpView from '$lib/components/views/HelpView.svelte';

	const frames: Record<Frame, typeof DashbosrdView> = {
	    dashboard: DashboardView,
	    users: UsersView,
	    courses: CoursesView,
	    analytics: AnalyticsView,
	    account: AccountView,
	    help: HelpView
	  };
</script>

<svelte:component this={frames[$currentFrame]} />

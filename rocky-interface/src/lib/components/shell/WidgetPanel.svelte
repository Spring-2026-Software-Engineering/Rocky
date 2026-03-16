<script>
	import WidgetCard from './WidgetCard.svelte';
</script>

<div class="widget-panel">

	<h2 class="widget-panel-title">Widgets</h2>

<WidgetCard title="Analytics">
	<p>Total System Usage: 98%</p>
	<p>Active Requests: 42</p>
	<p>System Temp: 77deg</p>
</WidgetCard>

<WidgetCard title="System Info">
	<p>Limit Usage: 88%</p>
	<p>Courses: 3</p>
</WidgetCard>

<WidgetCard title="Notifications">
	<p>No new Notifications</p>
</WidgetCard>

</div>
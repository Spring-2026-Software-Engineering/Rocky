export type KpiMetric = {
	label: string;
	value: string;
	delta: string;
};

export type ActivityRow = {
	window: string;
	requests: number;
	flagged: number;
	successRate: string;
};

export function toKpiMetric(metric: Partial<KpiMetric>): KpiMetric {
	return {
		label: metric.label?.trim() || 'Unknown KPI',
		value: metric.value?.trim() || '0',
		delta: metric.delta?.trim() || '0%'
	};
}

export function toActivityRow(row: Partial<ActivityRow>): ActivityRow {
	return {
		window: row.window?.trim() || 'N/A',
		requests: typeof row.requests === 'number' && Number.isFinite(row.requests) ? row.requests : 0,
		flagged: typeof row.flagged === 'number' && Number.isFinite(row.flagged) ? row.flagged : 0,
		successRate: row.successRate?.trim() || '0%'
	};
}

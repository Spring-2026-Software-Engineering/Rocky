export type PanelWidget = {
	title: string;
	html?: string;
	lines?: string[];
};
export function toPanelWidget(widget: Partial<PanelWidget>): PanelWidget {
	return {
		title: widget.title?.trim() || 'Untitled Widget',
		html: widget.html?.trim(),
		lines: widget.lines?.filter((line) => line.trim().length > 0)
	};
}

export function toPanelWidgets(widgets: Array<Partial<PanelWidget>>): PanelWidget[] {
	return widgets.map(toPanelWidget);
}

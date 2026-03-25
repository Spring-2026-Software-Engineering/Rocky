export type ApiFaqItem = Partial<{
	question: string;
	answer: string;
}>;

export type FaqItem = {
	question: string;
	answer: string;
};

export function normalizeFaqItem(raw: ApiFaqItem): FaqItem {
	return {
		question: raw.question?.trim() || 'Question unavailable',
		answer: raw.answer?.trim() || 'Answer unavailable'
	};
}

export function normalizeFaqItems(rawItems: ApiFaqItem[]): FaqItem[] {
	return rawItems.map(normalizeFaqItem);
}
<script lang="ts">
	import { tick } from 'svelte';
	import '$lib/styles/routes/modules/credits-view.css';

	type Credit = {
		name: string;
		title: string;
		variant?: 'navy' | 'gold';
	};

	const teamCredits: Credit[] = [
    { name: 'Branson', title: 'Project stakeholder', variant: 'gold' },
    { name: 'Ian Rohrbacher', title: 'Scrum master', variant: 'navy' },
    { name: 'Archie Horne', title: '(waiting for contribution submission)', variant: 'gold' },
    { name: 'Tasmia Jannat Shammi', title: '(waiting for contribution submission)', variant: 'navy' },
    { name: 'Zoe Eigenbrod', title: '(waiting for contribution submission)', variant: 'gold' },
    { name: 'Dovlet Gurbanov', title: '(waiting for contribution submission)', variant: 'navy' },
    { name: 'Ian Smaglinski', title: 'Account page, Credits page, API key generator and hasher, Bug Fixer.', variant: 'gold' },
    { name: 'Simran Gautam', title: '(waiting for contribution submission)', variant: 'navy' },
    { name: 'Chris Vuletich', title: '(waiting for contribution submission)', variant: 'gold' },
    { name: 'Savar Shrestha', title: '(waiting for contribution submission)', variant: 'navy' }
  ];

	const assetCredits: Credit[] = [
		{
			name: 'Kent State University',
			title: 'Main login image and Kent State logo',
			variant: 'gold'
		},
		{ name: 'Archie Horne', title: 'Profile pictures and Rocky logo', variant: 'navy' }
	];

	let isRolling = false;

	function getInitials(name: string): string {
		return name
			.split(' ')
			.filter(Boolean)
			.slice(0, 2)
			.map((part) => part[0]?.toUpperCase() ?? '')
			.join('');
	}

	async function startCreditsRoll(): Promise<void> {
		isRolling = false;
		await tick();
		isRolling = true;
	}

	function resetCreditsRoll(): void {
		isRolling = false;
	}

	function handleKeydown(event: KeyboardEvent): void {
		if (event.key.toLowerCase() === 'g') {
			if (isRolling) {
				resetCreditsRoll();
				return;
			}

			void startCreditsRoll();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<main class="credits-page">
	<div class="credits-ambient credits-ambient-one"></div>
	<div class="credits-ambient credits-ambient-two"></div>

	<section class="credits-shell" class:credits-rolling={isRolling}>
		<header class="credits-header">
			<img src="/ksu_horizontal_blue.png" alt="Kent State University" class="credits-logo" />
			<div class="credits-header-copy">
				<p class="credits-eyebrow">Rocky Interface</p>
				<h1>Credits</h1>
				<p class="credits-subtitle">The team, stakeholder, and assets behind the Rocky project.</p>
			</div>
			<img src="/rocky.svg" alt="Rocky logo" class="rocky-corner-logo" />
		</header>

		<div class="credits-gold-rule"></div>

		<div class="credits-stage" aria-live="polite">
			<div class="credits-list">
				<div class="section-label">
					<span>Project Team</span>
				</div>

				{#each teamCredits as credit}
					<article class:credit-card-gold={credit.variant === 'gold'} class="credit-card">
						<div class="credit-initials" aria-hidden="true">{getInitials(credit.name)}</div>
						<div>
							<h2>{credit.name}</h2>
							<p>{credit.title}</p>
						</div>
					</article>
				{/each}

				<div class="section-label section-label-assets">
					<span>Asset Credits</span>
				</div>

				{#each assetCredits as credit}
					<article
						class:credit-card-gold={credit.variant === 'gold'}
						class="credit-card credit-card-asset"
					>
						<div class="credit-initials" aria-hidden="true">{getInitials(credit.name)}</div>
						<div>
							<h2>{credit.name}</h2>
							<p>{credit.title}</p>
							{#if credit.name === 'Kent State University'}
								<a href="https://www.kent.edu/">kent.edu</a>
							{/if}
						</div>
					</article>
				{/each}

				<p class="credits-finale">Thank you for using Rocky.</p>
			</div>
		</div>

		<footer class="credits-footer">
			<div class="credits-links">
				<a href="https://www.kent.edu/">Kent State</a>
				<a href="https://support.kent.edu/">Support</a>
				<a href="https://www.kent.edu/privacy-statement#cookies">Privacy</a>
			</div>

			<div class="credits-actions">
				<a class="signin-link" href="/login">Back to sign in</a>
				<button
					class="roll-button"
					type="button"
					onclick={isRolling ? resetCreditsRoll : startCreditsRoll}
				>
					{#if isRolling}
						Reset Credits
					{:else}
						Roll Credits
					{/if}
				</button>
			</div>
		</footer>
	</section>
</main>

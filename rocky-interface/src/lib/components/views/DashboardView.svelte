<script lang="ts">
  import CourseCard from '$lib/components/cards/CourseCard.svelte';
  import '$lib/styles/dashboard.css';

  type ViewMode = 'card' | 'list';
  let viewMode: ViewMode = 'card';
  let showViewMenu = false;

  // Placeholder course data
  const courses = [
    { id: 1, code: 'SE 3010', name: 'Software Engineering I', instructor: 'Dr. Alicia Moreno', color: '#1a4a8a' },
    { id: 2, code: 'CS 2410', name: 'Data Structures & Algorithms', instructor: 'Prof. Marcus Chen', color: '#7b2d8b' },
    { id: 3, code: 'CS 3560', name: 'Database Systems', instructor: 'Dr. Priya Narayanan', color: '#2d6a4f' },
    { id: 4, code: 'CS 3200', name: 'Operating Systems', instructor: 'Prof. Evan Brooks', color: '#c05621' },
    { id: 5, code: 'MATH 2280', name: 'Discrete Mathematics', instructor: 'Dr. Hannah Reed', color: '#155e75' },
    { id: 6, code: 'CS 3620', name: 'Computer Networks', instructor: 'Prof. Samuel Ortiz', color: '#7f1d1d' },
    { id: 7, code: 'CS 3810', name: 'Human-Computer Interaction', instructor: 'Dr. Lily Park', color: '#3b0764' },
    { id: 8, code: 'CS 4990', name: 'Senior Capstone Project', instructor: 'Prof. Jordan Patel', color: '#14532d' },
  ];

  function setView(mode: ViewMode) {
    viewMode = mode;
    showViewMenu = false;
  }
</script>

<div class="dashboard-wrapper">
  <div class="dashboard-header">
    <h1>Dashboard</h1>
    <div class="view-switcher">
      <button class="view-btn" on:click={() => showViewMenu = !showViewMenu}>
        View
        <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="6 9 12 15 18 9"></polyline>
        </svg>
      </button>

      {#if showViewMenu}
        <div class="view-menu-backdrop" on:click={() => showViewMenu = false}></div>
        <div class="view-menu">
          <button class="view-option" class:active={viewMode === 'card'} on:click={() => setView('card')}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <rect x="3" y="3" width="7" height="7"></rect>
              <rect x="14" y="3" width="7" height="7"></rect>
              <rect x="14" y="14" width="7" height="7"></rect>
              <rect x="3" y="14" width="7" height="7"></rect>
            </svg>
            Card
          </button>
          <button class="view-option" class:active={viewMode === 'list'} on:click={() => setView('list')}>
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="8" y1="6" x2="21" y2="6"></line>
              <line x1="8" y1="12" x2="21" y2="12"></line>
              <line x1="8" y1="18" x2="21" y2="18"></line>
              <line x1="3" y1="6" x2="3.01" y2="6"></line>
              <line x1="3" y1="12" x2="3.01" y2="12"></line>
              <line x1="3" y1="18" x2="3.01" y2="18"></line>
            </svg>
            List
          </button>
        </div>
      {/if}
    </div>
  </div>

  <div class="dashboard-scroll-area">
    {#if viewMode === 'card'}
      <div class="courses-grid">
        {#each courses as course}
          <CourseCard {course} mode="card" />
        {/each}
      </div>
    {:else}
      <div class="courses-list">
        {#each courses as course}
          <CourseCard {course} mode="list" />
        {/each}
      </div>
    {/if}
  </div>
</div>


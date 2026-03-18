<script lang="ts">
  import CourseCard from '$lib/components/CourseCard.svelte';

  type ViewMode = 'card' | 'list';
  let viewMode: ViewMode = 'card';
  let showViewMenu = false;

  // Placeholder course data
  const courses = [
    { id: 1, code: '...', name: '...', instructor: '...', color: '#1a4a8a' },
    { id: 2, code: '...', name: '...', instructor: '...', color: '#7b2d8b' },
    { id: 3, code: '...', name: '...', instructor: '...', color: '#2d6a4f' },
    { id: 4, code: '...', name: '...', instructor: '...', color: '#c05621' },
    { id: 5, code: '...', name: '...', instructor: '...', color: '#155e75' },
    { id: 6, code: '...', name: '...', instructor: '...', color: '#7f1d1d' },
    { id: 7, code: '...', name: '...', instructor: '...', color: '#3b0764' },
    { id: 8, code: '...', name: '...', instructor: '...', color: '#14532d' },
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

<style>
  .dashboard-wrapper {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 24px 28px;
    box-sizing: border-box;
    overflow: hidden;
  }

  .dashboard-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 20px;
    flex-shrink: 0;
  }

  h1 {
    font-size: 1.6rem;
    font-weight: 600;
    color: #1a1a1a;
    margin: 0;
  }


  .view-switcher {
    position: relative;
  }

  .view-btn {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 7px 14px;
    background: #fff;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    font-size: 0.875rem;
    font-weight: 500;
    color: #374151;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }

  .view-btn:hover {
    background: #f3f4f6;
    border-color: #9ca3af;
  }

  .view-menu-backdrop {
    position: fixed;
    inset: 0;
    z-index: 10;
  }

  .view-menu {
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    background: #fff;
    border: 1px solid #e5e7eb;
    border-radius: 8px;
    box-shadow: 0 4px 16px rgba(0,0,0,0.1);
    z-index: 20;
    min-width: 140px;
    overflow: hidden;
  }

  .view-option {
    display: flex;
    align-items: center;
    gap: 10px;
    width: 100%;
    padding: 10px 16px;
    background: none;
    border: none;
    font-size: 0.875rem;
    color: #374151;
    cursor: pointer;
    transition: background 0.12s;
    text-align: left;
  }

  .view-option:hover {
    background: #f3f4f6;
  }

  .view-option.active {
    background: #eff6ff;
    color: #1d4ed8;
    font-weight: 600;
  }


  .dashboard-scroll-area {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding-right: 6px;
  }

  .dashboard-scroll-area::-webkit-scrollbar {
    width: 6px;
  }

  .dashboard-scroll-area::-webkit-scrollbar-track {
    background: transparent;
  }

  .dashboard-scroll-area::-webkit-scrollbar-thumb {
    background: #d1d5db;
    border-radius: 3px;
  }


  .courses-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 20px;
    padding-bottom: 24px;
  }


  .courses-list {
    display: flex;
    flex-direction: column;
    gap: 0;
    padding-bottom: 24px;
  }
</style>
<script lang="ts">
    import '$lib/styles/course-page.css';

    type Tab = 'home' | 'edit-courses' | 'edit-people' | 'graphs';
    let activeTab: Tab = 'edit-people';

    type Role = 'Instructor' | 'Student';
    interface Person {
        id: number;
        name: string;
        role: Role;
    }

    let people: Person[] = [
        { id: 1, name: 'Dr. Khan', role: 'Instructor' },
        { id: 2, name: 'Me', role: 'Student' },
        { id: 3, name: 'Me 2', role: 'Student' },
        { id: 4, name: 'Me 3', role: 'Student' },
    ];

    function removePerson(id: number) {
        people = people.filter(p => p.id !== id);
    }

    function upload() {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.csv';
        input.onchange = (e) => {
            const file = (e.target as HTMLInputElement).files?.[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (ev) => {
                const lines = (ev.target?.result as string).split('\n').slice(1);
                const imported: Person[] = lines
                    .filter(l => l.trim())
                    .map((l, i) => {
                        const [name, role] = l.split(',');
                        return { id: Date.now() + i, name: name?.trim() ?? '', role: (role?.trim() === 'Instructor' ? 'Instructor' : 'Student') as Role };
                    });
                people = [...people, ...imported];
            };
            reader.readAsText(file);
        };
        input.click();
    }

    function addPerson() {
        const name = prompt('Enter name:');
        if (!name?.trim()) return;
        const roleInput = prompt('Role (Instructor or Student):') ?? 'Student';
        const role: Role = roleInput.trim() === 'Instructor' ? 'Instructor' : 'Student';
        people = [...people, { id: Date.now(), name: name.trim(), role }];
    }
</script>

<div class="courses-wrapper">
  <!-- Tabs -->
  <div class="tabs">
    <button class="tab" class:active={activeTab === 'home'} on:click={() => activeTab = 'home'}>Home</button>
    <button class="tab" class:active={activeTab === 'edit-courses'} on:click={() => activeTab = 'edit-courses'}>Edit Courses</button>
    <button class="tab" class:active={activeTab === 'edit-people'} on:click={() => activeTab = 'edit-people'}>Edit People</button>
    <button class="tab" class:active={activeTab === 'graphs'} on:click={() => activeTab = 'graphs'}>Graphs</button>
  </div>

  <!-- Tab content -->
  <div class="tab-content">
    {#if activeTab === 'home'}
      <p class="placeholder-text">Select a tab to manage this course.</p>

    {:else if activeTab === 'edit-courses'}
      <p class="placeholder-text">Course editing coming soon.</p>

    {:else if activeTab === 'edit-people'}
      <div class="people-panel">
        <!-- Action bar -->
        <div class="action-bar">
          <button class="action-btn upload" on:click={upload}>
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
              <polyline points="17 8 12 3 7 8"></polyline>
              <line x1="12" y1="3" x2="12" y2="15"></line>
            </svg>
            Upload
          </button>
          <button class="action-btn add" on:click={addPerson}>
            <svg xmlns="http://www.w3.org/2000/svg" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <line x1="12" y1="5" x2="12" y2="19"></line>
              <line x1="5" y1="12" x2="19" y2="12"></line>
            </svg>
            Add
          </button>
        </div>

        <!-- People list -->
        <div class="people-list">
          {#if people.length === 0}
            <p class="empty-msg">No people in this course yet.</p>
          {:else}
            {#each people as person (person.id)}
              <div class="person-row">
                <span class="person-name">{person.name}</span>
                <span class="role-badge" class:instructor={person.role === 'Instructor'} class:student={person.role === 'Student'}>
                  {person.role}
                </span>
                <button class="delete-btn" on:click={() => removePerson(person.id)} aria-label="Remove {person.name}">
                  <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18"></line>
                    <line x1="6" y1="6" x2="18" y2="18"></line>
                  </svg>
                </button>
              </div>
            {/each}
          {/if}
        </div>
      </div>

    {:else if activeTab === 'graphs'}
      <p class="placeholder-text">Analytics graphs coming soon.</p>
    {/if}
  </div>
</div>
<script lang="ts">
  import '$lib/styles/components/course-card.css';
  import { createEventDispatcher } from 'svelte';
  
  export let course: {
    id: number;
    code: string;
    name: string;
    instructor: string;
    semester: string;
    color: string;
  };
  export let mode: 'card' | 'list' = 'card';

  const dispatch = createEventDispatcher<{ open: { courseId: number } }>();

  function openCourse() {
    dispatch('open', { courseId: course.id });
  }

  $: courseHexColor = course.color?.trim() || '#334155';
</script>

{#if mode === 'card'}
  <div class="course-card" role="button" tabindex="0" on:click={openCourse} on:keydown={(event) => (event.key === 'Enter' || event.key === ' ' ? openCourse() : null)}>
    <div class="card-banner" style={`background-color: ${courseHexColor};`}></div>
    <div class="card-body">
      <p class="course-name">{course.name}</p>
      <p class="course-meta">{course.code} · {course.semester}</p>
    </div>
    <div class="card-footer">
      <button type="button" class="go-btn" on:click|stopPropagation={openCourse}>Go to Course →</button>
    </div>
  </div>
{:else}
  <div class="list-row" role="button" tabindex="0" on:click={openCourse} on:keydown={(event) => (event.key === 'Enter' || event.key === ' ' ? openCourse() : null)}>
    <div class="list-color-bar" style={`background-color: ${courseHexColor};`}></div>
    <div class="list-course-icon" style={`background-color: ${courseHexColor};`}>
      {course.code.slice(0, 2)}
    </div>
    <div class="list-info">
      <p class="list-course-name">{course.name}</p>
      <p class="list-course-meta">{course.code} · {course.semester}</p>
    </div>
    <button type="button" class="list-go-btn" on:click|stopPropagation={openCourse}>Go →</button>
  </div>
{/if}

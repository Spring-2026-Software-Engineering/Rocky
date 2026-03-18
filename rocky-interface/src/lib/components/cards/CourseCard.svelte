<script lang="ts">
  import '$lib/styles/course-card.css';
  
  export let course: {
    id: number;
    code: string;
    name: string;
    instructor: string;
    color: string;
  };
  export let mode: 'card' | 'list' = 'card';
</script>

{#if mode === 'card'}
  <div class="course-card">
    <div class="card-banner" style="background-color: {course.color};">
      <span class="course-code">{course.code}</span>
    </div>
    <div class="card-body">
      <p class="course-name">{course.name}</p>
      <p class="instructor">{course.instructor}</p>
    </div>
    <div class="card-footer">
      <button class="go-btn">Go to Course →</button>
    </div>
  </div>
{:else}
  <div class="list-row">
    <div class="list-color-bar" style="background-color: {course.color};"></div>
    <div class="list-course-icon" style="background-color: {course.color};">
      {course.code.slice(0, 2)}
    </div>
    <div class="list-info">
      <p class="list-course-name">{course.name}</p>
      <p class="list-course-meta">{course.code} · {course.instructor}</p>
    </div>
    <button class="list-go-btn">Go →</button>
  </div>
{/if}

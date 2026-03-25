<script lang="ts">
  import '$lib/styles/course-card.css';
  
  export let course: {
    id: number;
    code: string;
    name: string;
    instructor: string;
    semester: string;
    color: string;
  };
  export let mode: 'card' | 'list' = 'card';

  $: courseHexColor = course.color?.trim() || '#334155';
</script>

{#if mode === 'card'}
  <div class="course-card">
    <div class="card-banner" style={`background-color: ${courseHexColor};`}></div>
    <div class="card-body">
      <p class="course-name">{course.name}</p>
      <p class="course-meta">{course.code} · {course.semester}</p>
    </div>
    <div class="card-footer">
      <button class="go-btn">Go to Course →</button>
    </div>
  </div>
{:else}
  <div class="list-row">
    <div class="list-color-bar" style={`background-color: ${courseHexColor};`}></div>
    <div class="list-course-icon" style={`background-color: ${courseHexColor};`}>
      {course.code.slice(0, 2)}
    </div>
    <div class="list-info">
      <p class="list-course-name">{course.name}</p>
      <p class="list-course-meta">{course.code} · {course.semester}</p>
    </div>
    <button class="list-go-btn">Go →</button>
  </div>
{/if}

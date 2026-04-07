 <script lang="ts">

  import { page } from '$app/state';

  import { goto } from '$app/navigation';

  import { setThemePreference } from '$lib/stores/themeStore';

  import type { ThemePreference } from '$lib/settings/userSettings';


  let toggled = $state(page.data.themePreference === 'dark');


  const user = {

    name: "Admin Istrator",

    id: "123456789",

    email: "example@kent.edu",

    role: "Administrator"

  };


  async function handleToggle() {

    toggled = !toggled;

    const newTheme: ThemePreference = toggled ? 'dark' : 'light';

    try {

      await setThemePreference(newTheme);

    } catch (err) {

      toggled = !toggled;

    }

  }


  function logout() {

    void goto('/logout');

  }

</script>


<div class="view-container">

  <header class="header-section">

    <div class="header-left">

      <h1 class="main-title" class:is-dark-text={toggled}>Account Profile</h1>

      <p class="sub-title">View your account details and manage your display preferences.</p>

    </div>

    <div class="header-right">

      <button class="logout-btn" onclick={logout}>Log Out</button>

    </div>

  </header>


  <div class="account-card" class:is-dark-card={toggled}>

    <div class="card-content-top">

      <div class="avatar-circle" class:dark-bubble-match={toggled}>

        <svg viewBox="0 0 24 24" fill={toggled.value ? "var(--color-gray-400)" : "var(--color-gray-300)"} width="100%" height="100%">

          <path d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/>

        </svg>

      </div>


      <div class="user-info">

        <h2 class="display-name">{user.name}</h2>

        <div class="info-grid">

          <p><strong>ID:</strong> {user.id}</p>

          <p><strong>Email:</strong> {user.email}</p>

          <p><strong>Role:</strong> {user.role}</p>

        </div>

      </div>

    </div>


    <hr class="divider" />


    <div class="card-content-bottom">

      <div class="setting-text">

        <p class="setting-label">Dark Mode</p>

        <p class="setting-hint">Adjust the appearance of the interface.</p>

      </div>

      <div class="toggle-wrapper">

        <button

          type="button"

          class="toggle-switch"

          class:is-active={toggled}

          onclick={handleToggle}

          aria-label="Toggle Dark Mode"

        >

        </button>

      </div>

    </div>

  </div>

</div>


<style>

  .view-container {

    padding: var(--space-4xl);

    width: 100%;

    min-height: 100vh;

    box-sizing: border-box;

    display: flex;

    flex-direction: column;

    align-items: flex-start;

  }


  .header-section {

    display: flex;

    justify-content: space-between;

    align-items: flex-start;

    margin-bottom: var(--space-3xl);

    width: 100%;

  }


  .main-title {

    font-size: var(--font-size-3xl);

    font-weight: var(--font-weight-bold);

    margin: 0;

    font-family: var(--font-family-base);

    color: var(--color-gray-900);

    transition: color var(--transition-slow);

  }

 

  .main-title.is-dark-text {

    color: var(--color-white);

  }


  .sub-title {

    font-size: var(--font-size-base);

    margin-top: var(--space-sm);

    font-family: var(--font-family-base);

    color: var(--color-gray-600);

  }


  .logout-btn {

    background-color: #ef4444;

    color: var(--color-white);

    border: none;

    padding: var(--space-sm) var(--space-xl);

    border-radius: var(--radius-sm);

    font-weight: var(--font-weight-bold);

    cursor: pointer;

    transition: background var(--transition-fast);

  }


  .account-card {

    background-color: var(--color-white);

    border-radius: var(--radius-xl);

    padding: var(--space-4xl);

    width: 100%;

    box-sizing: border-box;

    box-shadow: var(--shadow-lg);

    border: 1px solid var(--color-gray-200);

    transition: all var(--transition-slow);

    color: var(--color-gray-900);

  }


  .account-card.is-dark-card {

    background-color: #222833;

    color: var(--color-text-primary);

    border-color: #2f3744;

  }


  .card-content-top {

    display: flex;

    align-items: center;

    gap: var(--space-3xl);

  }


  .avatar-circle {

    width: 100px;

    height: 100px;

    background: var(--color-gray-100);

    border-radius: 50%;

    display: flex;

    align-items: center;

    justify-content: center;

    flex-shrink: 0;

    transition: background-color var(--transition-slow);

  }

 

  .dark-bubble-match {

    background-color: #222833 !important;

    border: 1px solid #465062;

  }


  .display-name {

    font-size: var(--font-size-3xl);

    font-weight: var(--font-weight-bold);

    margin: 0;

  }


  .info-grid {

    margin-top: var(--space-sm);

    color: var(--color-text-secondary);

  }


  .is-dark-card .info-grid p strong {

    color: var(--color-white);

  }


  .divider {

    border: 0;

    border-top: 1px solid var(--color-gray-200);

    margin: var(--space-3xl) 0;

  }


  .is-dark-card .divider {

    border-top-color: var(--color-gray-300);

  }


  .card-content-bottom {

    display: flex;

    justify-content: space-between;

    align-items: center;

  }


  .setting-label {

    font-size: var(--font-size-xl);

    font-weight: var(--font-weight-bold);

    margin: 0;

  }


  .setting-hint {

    color: var(--color-text-secondary);

    font-size: var(--font-size-sm);

    margin-top: var(--space-xs);

  }


  .toggle-switch {

    width: 52px;

    height: 28px;

    background: var(--color-gray-300);

    border: 2px solid var(--color-gray-400);

    border-radius: 20px;

    position: relative;

    cursor: pointer;

    padding: 0;

    transition: all var(--transition-base);

  }


  .toggle-switch::after {

    content: '';

    position: absolute;

    top: 2px;

    left: 2px;

    width: 20px;

    height: 20px;

    background: var(--color-white);

    border-radius: 50%;

    box-shadow: var(--shadow-sm);

    transition: transform var(--transition-slow) cubic-bezier(0.4, 0, 0.2, 1);

  }


  .toggle-switch.is-active {

    background-color: var(--color-accent);

    border-color: var(--color-accent);

  }


  .toggle-switch.is-active::after {

    transform: translateX(24px);

  }

</style> 
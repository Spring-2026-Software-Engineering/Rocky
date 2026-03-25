<script lang="ts">
	import '$lib/styles/login.css';
</script>

<div class="login-background">
  <div class="login-overlay">
    <div class="login-shell">
      <section class="login-column">
        <div class="login-top">
          <img src="/ksu_horizontal.png" alt="Kent State University" class="login-ksu-logo" />
          <h1 class="login-title">Sign in to Rocky</h1>
          <a class="login-signin-btn" href="/login/preview">Sign In</a>
          <p class="login-help-links">
            Forgot your <a href="/login/preview">Username</a> or <a href="/login/preview">Password</a>?
          </p>
        </div>

        <div class="login-bottom">
          <p>If this is your first time logging in, please visit <a href="https://welcome.kent.edu/">welcome.kent.edu</a>.</p>
          <p>If you need assistance, please visit <a href="https://support.kent.edu/">support.kent.edu</a> to chat with the Helpdesk.</p>
        </div>
      </section>
    </div>

    <footer class="login-footer">
      <a href="https://www.kent.edu/privacy-statement#cookies">Privacy and cookies</a>
    </footer>
  </div>
</div>

<script lang="ts">
  import { browser } from '$app/environment';
  import { ENABLE_MICROSOFT_OAUTH, ENABLE_PREVIEW_AUTH, MICROSOFT_OAUTH } from '$lib/config/env';
  import '$lib/styles/routes/login.css';

  type MsalClaims = Record<string, unknown>;

  let error: string | null = null;
  let isSigningInWithMicrosoft = false;

  function readClaim(claims: MsalClaims | undefined, ...keys: string[]): string {
    if (!claims) {
      return '';
    }

    for (const key of keys) {
      const value = claims[key];
      if (typeof value === 'string' && value.trim()) {
        return value.trim();
      }
    }

    return '';
  }

  async function signInWithMicrosoft(): Promise<void> {
    if (!browser || !ENABLE_MICROSOFT_OAUTH || isSigningInWithMicrosoft) {
      return;
    }

    error = null;
    isSigningInWithMicrosoft = true;

    try {
      const { PublicClientApplication } = await import('@azure/msal-browser');
      const app = new PublicClientApplication({
        auth: {
          clientId: MICROSOFT_OAUTH.clientId,
          authority: MICROSOFT_OAUTH.authority,
          redirectUri: new URL('/login', window.location.origin).toString()
        },
        cache: {
          cacheLocation: 'sessionStorage'
        }
      });

      await app.initialize();
      const loginResponse = await app.loginPopup({
        scopes: ['openid', 'profile', 'email', 'User.Read'],
        prompt: 'select_account'
      });

      const claims = (loginResponse.idTokenClaims ?? {}) as MsalClaims;
      console.log('[oauth] microsoft id token claims', claims);

      const email =
        readClaim(claims, 'preferred_username', 'email', 'upn', 'unique_name') ||
        (loginResponse.account?.username ?? '').trim();
      const firstName = readClaim(claims, 'given_name', 'name');
      const lastName = readClaim(claims, 'family_name');
      const id = readClaim(claims, 'id', 'ksuid', 'employeeId', 'extension_KSUID', 'extension_ksuid');

      if (!email) {
        throw new Error('Microsoft login returned no usable email claim.');
      }

      const sessionResponse = await fetch('/auth/microsoft/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          firstName,
          lastName,
          email,
          id
        })
      });

      if (!sessionResponse.ok) {
        const payload = (await sessionResponse.json().catch(() => ({ error: 'Unable to sign in with Microsoft.' }))) as {
          error?: string;
        };
        throw new Error(payload.error || 'Unable to sign in with Microsoft.');
      }

      console.log('[oauth] frontend session established', { email });
      window.location.href = '/';
    } catch (err) {
      console.log('[oauth] frontend sign-in failed', err);
      error = err instanceof Error ? err.message : 'Unable to sign in with Microsoft.';
    } finally {
      isSigningInWithMicrosoft = false;
    }
  }
</script>

<div class="login-background">
  <div class="login-overlay">
    <div class="login-shell">
      <section class="login-column">
        <div class="login-top">
          <img src="/ksu_horizontal_blue.png" alt="Kent State University" class="login-ksu-logo" />
          <h1 class="login-title">Sign in to Rocky</h1>
          {#if ENABLE_MICROSOFT_OAUTH}
            <button class="login-signin-btn" type="button" onclick={signInWithMicrosoft} disabled={isSigningInWithMicrosoft}>
              {isSigningInWithMicrosoft ? 'Signing In...' : 'Sign In'}
            </button>
          {:else if ENABLE_PREVIEW_AUTH}
            <a class="login-signin-btn" href="/login/preview">Sign In</a>
          {/if}
          {#if error}
            <p class="login-error">{error}</p>
          {/if}
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

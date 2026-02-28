<script lang="ts">
  import { api } from '../api/client';
  import { push } from 'svelte-spa-router';

  let username = '';
  let password = '';
  let error = '';
  let loading = false;
  let allowNewUsers = true;

  async function checkRegistration() {
    try {
      const config = await api.getEnvConfig();
      allowNewUsers = config.ALLOW_NEW_USERS === true || config.ALLOW_NEW_USERS === 'true';
    } catch (e) {
      console.error('Failed to check registration status:', e);
    }
  }

  checkRegistration();

  async function handleSubmit() {
    error = '';
    loading = true;

    try {
      await api.login(username, password);
      push('/dashboard');
      window.location.reload();
    } catch (e: any) {
      error = e.message || 'Login failed';
    } finally {
      loading = false;
    }
  }
</script>

<div class="min-h-screen flex items-center justify-center p-4">
  <div class="glass-card w-full max-w-md animate-scaleIn">
    <div class="text-center mb-6">
      <div class="brand-icon mx-auto mb-4">
        <span class="text-2xl">▶</span>
      </div>
      <h1 class="text-2xl font-bold">yt-dlp Manager</h1>
      <p class="opacity-75 mt-2">Sign in to your account</p>
    </div>

    <form on:submit|preventDefault={handleSubmit} class="flex flex-col gap-4">
      <div>
        <label for="username">Username</label>
        <input
          type="text"
          id="username"
          bind:value={username}
          placeholder="Enter your username"
          required
          class="glass-input"
        />
      </div>

      <div>
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          bind:value={password}
          placeholder="Enter your password"
          required
          class="glass-input"
        />
      </div>

      {#if error}
        <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30">
          <p class="text-red-300 text-sm">{error}</p>
        </div>
      {/if}

      <button type="submit" class="glass-btn glass-btn-primary w-full mt-2" disabled={loading}>
        {#if loading}
          <span class="inline-block w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mr-2"></span>
        {/if}
        Sign In
      </button>
    </form>

    {#if allowNewUsers}
      <p class="text-center mt-6 opacity-75">
        Don't have an account? <a href="#/register" class="text-blue-400 hover:text-blue-300">Register</a>
      </p>
    {:else}
      <p class="text-center mt-6 opacity-75">
        Don't have an account? Contact an administrator.
      </p>
    {/if}
  </div>
</div>

<style>
  .brand-icon {
    width: 64px;
    height: 64px;
    background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
    border-radius: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 24px rgba(0, 122, 255, 0.4);
  }
</style>

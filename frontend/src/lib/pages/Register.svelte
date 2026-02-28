<script lang="ts">
  import { api } from '../api/client';
  import { push } from 'svelte-spa-router';

  let username = '';
  let email = '';
  let password = '';
  let confirmPassword = '';
  let error = '';
  let loading = false;

  let errors: Record<string, string> = {};

  function validateEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  function validateUsername(username: string): boolean {
    return username.length >= 3 && username.length <= 30 && /^[a-zA-Z0-9_]+$/.test(username);
  }

  async function handleSubmit() {
    error = '';
    errors = {};

    if (!username.trim()) {
      errors.username = 'Username is required';
    } else if (!validateUsername(username)) {
      errors.username = 'Username must be 3-30 characters, alphanumeric and underscores only';
    }

    if (!email.trim()) {
      errors.email = 'Email is required';
    } else if (!validateEmail(email)) {
      errors.email = 'Please enter a valid email address (e.g., user@example.com)';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 6) {
      errors.password = 'Password must be at least 6 characters';
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (Object.keys(errors).length > 0) {
      return;
    }

    loading = true;

    try {
      await api.register(username, email, password);
      await api.login(username, password);
      push('/dashboard');
      window.location.reload();
    } catch (e: any) {
      error = e.message || 'Registration failed';
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
      <h1 class="text-2xl font-bold">Create Account</h1>
      <p class="opacity-75 mt-2">Join yt-dlp Manager</p>
    </div>

    <form on:submit|preventDefault={handleSubmit} class="flex flex-col gap-4">
      <div>
        <label for="username">Username</label>
        <input
          type="text"
          id="username"
          bind:value={username}
          placeholder="Choose a username (3-30 chars, alphanumeric)"
          required
          class="glass-input"
          class:!border-red-500={errors.username}
        />
        {#if errors.username}
          <p class="text-red-400 text-xs mt-1">{errors.username}</p>
        {/if}
      </div>

      <div>
        <label for="email">Email</label>
        <input
          type="email"
          id="email"
          bind:value={email}
          placeholder="Enter your email (e.g., user@example.com)"
          required
          class="glass-input"
          class:!border-red-500={errors.email}
        />
        {#if errors.email}
          <p class="text-red-400 text-xs mt-1">{errors.email}</p>
        {/if}
      </div>

      <div>
        <label for="password">Password</label>
        <input
          type="password"
          id="password"
          bind:value={password}
          placeholder="Create a password (min 6 characters)"
          required
          class="glass-input"
          class:!border-red-500={errors.password}
        />
        {#if errors.password}
          <p class="text-red-400 text-xs mt-1">{errors.password}</p>
        {/if}
      </div>

      <div>
        <label for="confirmPassword">Confirm Password</label>
        <input
          type="password"
          id="confirmPassword"
          bind:value={confirmPassword}
          placeholder="Confirm your password"
          required
          class="glass-input"
          class:!border-red-500={errors.confirmPassword}
        />
        {#if errors.confirmPassword}
          <p class="text-red-400 text-xs mt-1">{errors.confirmPassword}</p>
        {/if}
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
        Create Account
      </button>
    </form>

    <p class="text-center mt-6 opacity-75">
      Already have an account? <a href="#/login" class="text-blue-400 hover:text-blue-300">Sign in</a>
    </p>
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

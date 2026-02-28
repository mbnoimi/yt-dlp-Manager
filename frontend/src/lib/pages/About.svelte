<script lang="ts">
  import { onMount } from 'svelte';
  import { user } from '../stores/auth';
  import { api } from '../api/client';

  let appInfo: { title: string; description: string; version: string } | null = null;

  onMount(async () => {
    try {
      appInfo = await api.getAppInfo();
    } catch (e) {
      appInfo = { title: 'yt-dlp Manager', description: 'A powerful yt-dlp interface for multi-user audio/video downloading across thousands of supported sites.', version: 'Unknown' };
    }
  });
</script>

<div class="max-w-xl mx-auto stagger-children">
  <div class="glass-card text-center">
    <div class="brand-icon mx-auto mb-4">
      <span class="text-3xl">▶</span>
    </div>
    <h1 class="text-2xl font-bold">{appInfo?.title || 'yt-dlp Manager'}</h1>
    <p class="opacity-75 mt-2 mb-4">{appInfo?.description || 'A YouTube/video downloader built with FastAPI and yt-dlp'}</p>
    <div class="inline-block px-4 py-2 bg-white/10 rounded-full">
      <span class="font-mono">Version {appInfo?.version || '...'}</span>
    </div>
  </div>

  <div class="glass-card mt-6">
    <h3 class="font-semibold mb-4">Your Account</h3>
    <div class="flex flex-col gap-3">
      <div class="flex justify-between py-2 border-b border-white/10">
        <span class="opacity-75">Username</span>
        <span class="font-medium">{$user?.username}</span>
      </div>
      <div class="flex justify-between py-2 border-b border-white/10">
        <span class="opacity-75">Email</span>
        <span class="font-medium">{$user?.email}</span>
      </div>
      <div class="flex justify-between py-2">
        <span class="opacity-75">Role</span>
        <span>
          {#if $user?.is_admin}
            <span class="glass-badge glass-badge-info">Administrator</span>
          {:else}
            <span class="glass-badge glass-badge-success">User</span>
          {/if}
        </span>
      </div>
    </div>
  </div>

  <div class="glass-card mt-6">
    <h3 class="font-semibold mb-4">Quick Links</h3>
    <div class="flex flex-col gap-2">
      {#if $user?.is_admin}
        <a href="#/server-manager" class="glass-btn text-left">⚙️ Server Manager</a>
      {/if}
      <a href="#/dashboard" class="glass-btn text-left">📊 Dashboard</a>
      <a href="#/profile" class="glass-btn text-left">👤 Profile</a>
    </div>
  </div>
</div>

<style>
  .brand-icon {
    width: 80px;
    height: 80px;
    background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
    border-radius: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 32px rgba(0, 122, 255, 0.4);
  }
</style>

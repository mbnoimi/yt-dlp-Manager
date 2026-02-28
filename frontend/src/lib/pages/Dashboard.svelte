<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { api } from '../api/client';
  import { startSSE, stopSSE } from '../stores/downloads';
  
  import Datasources from './Dashboard/Datasources.svelte';
  import Scheduler from './Dashboard/Scheduler.svelte';
  import Logs from './Dashboard/Logs.svelte';
  import Files from './Dashboard/Files.svelte';

  let activeTab = 'datasources';
  let error = '';
  let success = '';

  onMount(async () => {
    const token = api.getToken();
    if (!token) return;
    
    try {
      await api.getMe();
    } catch {
      return;
    }
    
    startSSE();
  });

  onDestroy(() => {
    stopSSE();
  });
</script>

<div class="dashboard stagger-children">
  {#if error}
    <div class="glass-card !bg-red-500/20 border-red-500/30 p-4 flex justify-between items-center">
      <span class="text-red-300">{error}</span>
      <button class="opacity-75 hover:opacity-100" onclick={() => error = ''}>&times;</button>
    </div>
  {/if}

  {#if success}
    <div class="glass-card !bg-green-500/20 border-green-500/30 p-4">
      <span class="text-green-300">{success}</span>
    </div>
  {/if}

  <div class="glass-tabs">
    <button class="glass-tab" class:active={activeTab === 'datasources'} onclick={() => activeTab = 'datasources'}>
      Datasources
    </button>
    <button class="glass-tab" class:active={activeTab === 'scheduler'} onclick={() => activeTab = 'scheduler'}>
      Scheduler
    </button>
    <button class="glass-tab" class:active={activeTab === 'files'} onclick={() => activeTab = 'files'}>
      Files
    </button>
    <button class="glass-tab" class:active={activeTab === 'logs'} onclick={() => activeTab = 'logs'}>
      Logs
    </button>
  </div>

  {#if activeTab === 'datasources'}
    <div class="mt-6">
      <Datasources />
    </div>
  {:else if activeTab === 'scheduler'}
    <div class="mt-6">
      <Scheduler />
    </div>
  {:else if activeTab === 'files'}
    <div class="mt-6">
      <Files />
    </div>
  {:else if activeTab === 'logs'}
    <div class="mt-6">
      <Logs />
    </div>
  {/if}
</div>

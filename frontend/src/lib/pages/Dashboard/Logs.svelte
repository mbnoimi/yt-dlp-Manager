<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { user } from '../../stores/auth';
  import LogViewer from '../../components/LogViewer.svelte';

  let logs = $state('');
  let loading = $state(false);
  let error = $state('');
  let follow = $state(false);

  let logPath = $derived($user ? `data/${$user.username}/logs/user.log` : '');

  export async function loadLogs() {
    loading = true;
    error = '';
    try {
      logs = await api.getUserLogs();
    } catch (e: any) {
      error = e.message || 'Failed to load logs';
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadLogs();
  });
</script>

<div class="logs-page stagger-children">
  <div class="glass-card">
    <div class="flex justify-between items-center mb-4">
      <div class="flex gap-4 items-center">
        <h3 class="text-lg font-semibold">User Logs</h3>
        <span class="text-sm opacity-75">({logPath})</span>
      </div>
      <div class="flex gap-2">
        <button class="glass-btn" onclick={loadLogs} disabled={loading}>
          {loading ? 'Loading...' : '🔄 Refresh'}
        </button>
      </div>
    </div>

    {#if error}
      <div class="!p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}

    {#if loading}
      <div class="text-center py-8 opacity-75">Loading logs...</div>
    {:else if logs}
      <LogViewer 
        content={logs} 
        height="500px" 
        follow={follow}
        searchable={true}
        lineNumbers={true}
      />
    {:else}
      <div class="text-center py-8 opacity-75">No logs available</div>
    {/if}
  </div>
</div>

<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { showToast } from '../../stores/toasts';

  let systemInfo: any = null;
  let serverInfo: any = null;
  let loading = false;
  let upgrading = false;

  onMount(async () => {
    await loadData();
  });

  async function loadData() {
    loading = true;
    try {
      const [sys, srv] = await Promise.all([
        api.getSystemCheck(),
        api.getServerInfo()
      ]);
      systemInfo = sys;
      serverInfo = srv;
    } catch (e: any) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  async function upgradeYtDlp() {
    upgrading = true;
    try {
      const result = await api.upgradeYtDlp();
      showToast(result.message, result.success ? 'success' : 'error');
      await loadData();
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      upgrading = false;
    }
  }

  function formatBytes(bytes: number): string {
    const gb = bytes / (1024 * 1024 * 1024);
    return gb.toFixed(2) + ' GB';
  }
</script>

<div class="stagger-children">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-bold">System Status</h2>
    <button class="glass-btn" on:click={loadData} disabled={loading}>
      {loading ? 'Loading...' : '🔄 Refresh'}
    </button>
  </div>

  <div class="glass-card mb-6">
    <h3 class="font-semibold mb-4">🖥️ Server Information</h3>
    {#if serverInfo}
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div class="p-3 bg-white/5 rounded-lg">
          <div class="text-sm opacity-75">Platform</div>
          <div class="font-medium">{serverInfo.platform}</div>
        </div>
        <div class="p-3 bg-white/5 rounded-lg">
          <div class="text-sm opacity-75">Python</div>
          <div class="font-medium">{serverInfo.python_version}</div>
        </div>
        <div class="p-3 bg-white/5 rounded-lg">
          <div class="text-sm opacity-75">CPU Cores</div>
          <div class="font-medium">{serverInfo.cpu_count}</div>
        </div>
        <div class="p-3 bg-white/5 rounded-lg">
          <div class="text-sm opacity-75">Memory</div>
          <div class="font-medium">{formatBytes(serverInfo.memory_total)}</div>
        </div>
      </div>

      <div class="mt-4">
        <div class="flex justify-between mb-2">
          <span class="text-sm opacity-75">Memory Usage</span>
          <span class="text-sm">{formatBytes(serverInfo.memory_total - serverInfo.memory_available)} / {formatBytes(serverInfo.memory_total)}</span>
        </div>
        <div class="glass-progress">
          <div class="glass-progress-bar" style="width: {((serverInfo.memory_total - serverInfo.memory_available) / serverInfo.memory_total * 100).toFixed(1)}%"></div>
        </div>
      </div>

      <div class="mt-4">
        <div class="flex justify-between mb-2">
          <span class="text-sm opacity-75">Disk Usage</span>
          <span class="text-sm">{formatBytes(serverInfo.disk_used)} / {formatBytes(serverInfo.disk_total)}</span>
        </div>
        <div class="glass-progress">
          <div class="glass-progress-bar" style="width: {(serverInfo.disk_used / serverInfo.disk_total * 100).toFixed(1)}%"></div>
        </div>
      </div>
    {:else}
      <p class="opacity-75">Loading server info...</p>
    {/if}
  </div>

  <div class="glass-card">
    <h3 class="font-semibold mb-4">🔧 Tools Status</h3>
    <div class="flex flex-col gap-3">
      <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
        <span class="font-medium">yt-dlp</span>
        <div class="flex items-center gap-3">
          {#if systemInfo?.yt_dlp_installed}
            <span class="text-green-400">✓ {systemInfo.yt_dlp_version}</span>
            <button class="glass-btn text-sm" on:click={upgradeYtDlp} disabled={upgrading}>
              {upgrading ? 'Upgrading...' : 'Upgrade'}
            </button>
          {:else}
            <span class="text-red-400">✗ Not installed</span>
          {/if}
        </div>
      </div>
      <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
        <span class="font-medium">Deno</span>
        {#if systemInfo?.deno_installed}
          <span class="text-green-400">✓ {systemInfo.deno_version}</span>
        {:else}
          <span class="text-red-400">✗ Not installed</span>
        {/if}
      </div>
    </div>
  </div>
</div>

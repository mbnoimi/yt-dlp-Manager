<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { showToast } from '../../stores/toasts';
  import { openModal } from '../../stores/modal';
  import ConfirmDialog from '../../components/ConfirmDialog.svelte';

  type ConfigKey = string;
  type ConfigValue = string | number | boolean;

  let config: Record<ConfigKey, ConfigValue> | null = null;
  let loading = false;
  let saving = false;
  let error = '';
  let success = '';

  let restartLoading = false;
  let shutdownLoading = false;

  onMount(async () => {
    await loadConfig();
  });

  async function loadConfig() {
    loading = true;
    error = '';
    try {
      config = await api.getEnvConfig();
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }

  async function saveConfig() {
    if (!config) return;
    saving = true;
    error = '';
    success = '';
    try {
      const result = await api.updateEnvConfig(config);
      showToast(result.message, 'success');
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      saving = false;
    }
  }

  function restartServer() {
    openModal(ConfirmDialog, {
      title: 'Confirm Restart',
      message: 'Are you sure you want to restart the backend server? Users will experience a brief interruption.',
      confirmText: 'Restart',
      onConfirm: async () => {
        restartLoading = true;
        try {
          await api.restartServer();
          showToast('Server restarting...', 'info');
          
          await new Promise(r => setTimeout(r, 3000));
          
          try {
            await api.healthCheck();
            showToast('Server restarted successfully!', 'success');
            await loadConfig();
          } catch {
            showToast('Server restarted. Reloading page...', 'info');
            window.location.reload();
          }
        } catch (e: any) {
          showToast(e.message, 'error');
        } finally {
          restartLoading = false;
        }
      }
    });
  }

  function shutdownServer() {
    openModal(ConfirmDialog, {
      title: 'Confirm Shutdown',
      message: 'Are you sure you want to SHUTDOWN the backend server? The server will stop running and will need to be started manually.',
      confirmText: 'Shutdown',
      danger: true,
      onConfirm: async () => {
        shutdownLoading = true;
        try {
          await api.shutdownServer();
          showToast('Server shutting down...', 'info');
          
          let serverDown = false;
          for (let i = 0; i < 10; i++) {
            await new Promise(r => setTimeout(r, 1000));
            try {
              await api.healthCheck();
            } catch {
              serverDown = true;
              break;
            }
          }
          
          if (serverDown) {
            showToast('Server has been shut down. Please restart manually.', 'info');
          } else {
            showToast('Server did not shut down. Please stop manually.', 'error');
          }
        } catch (e: any) {
          showToast(e.message, 'error');
        } finally {
          shutdownLoading = false;
        }
      }
    });
  }

  function getFieldType(key: string, value: string | number | boolean): string {
    if (typeof value === 'boolean') {
      return 'boolean';
    }
    if (typeof value === 'number') {
      return 'number';
    }
    if (key.includes('PORT') || key.includes('DOWNLOADS') || key.includes('MAX_')) {
      return 'number';
    }
    if (key.includes('PASSWORD') || key.includes('SECRET')) {
      return 'password';
    }
    return 'text';
  }

  function formatLabel(key: string): string {
    return key.replace(/_/g, ' ').toLowerCase().replace(/\b\w/g, c => c.toUpperCase());
  }
</script>

<div class="stagger-children">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-bold">Environment Configuration</h2>
    <button class="glass-btn" on:click={loadConfig} disabled={loading}>
      {loading ? 'Loading...' : '🔄 Refresh'}
    </button>
  </div>

  {#if config}
    <div class="glass-card mb-6">
      <div class="flex flex-col gap-4">
        {#each Object.entries(config) as [key, value]}
          <div class="flex items-center justify-between gap-4">
            <label for={key} class="flex-1">{formatLabel(key)}</label>
            {#if getFieldType(key, value) === 'boolean'}
              <button 
                class="glass-toggle {value ? 'active' : ''}"
                on:click={() => { config![key] = !value }}
              ></button>
            {:else if getFieldType(key, value) === 'number'}
              <input 
                type="number" 
                class="glass-input !w-32"
                bind:value={config[key]} 
              />
            {:else if getFieldType(key, value) === 'password'}
              <input 
                type="password" 
                class="glass-input !w-64"
                bind:value={config[key]} 
              />
            {:else}
              <input 
                type="text" 
                class="glass-input !w-64"
                bind:value={config[key]} 
              />
            {/if}
          </div>
        {/each}
      </div>

      <div class="mt-6">
        <button class="glass-btn glass-btn-primary" on:click={saveConfig} disabled={saving}>
          {saving ? 'Saving...' : '💾 Save Configuration'}
        </button>
      </div>
    </div>

    <div class="glass-card !border-red-500/30">
      <h3 class="font-semibold mb-2">⚠️ Server Control</h3>
      <p class="text-sm opacity-75 mb-4">These actions affect the backend server directly.</p>
      
      <div class="flex gap-4">
        <button 
          class="glass-btn" 
          on:click={restartServer}
        >
          🔄 Restart Server
        </button>
        <button 
          class="glass-btn glass-btn-danger" 
          on:click={shutdownServer}
        >
          ⬛ Shutdown Server
        </button>
      </div>
    </div>
  {:else if loading}
    <div class="glass-card text-center py-8">
      <p class="opacity-75">Loading configuration...</p>
    </div>
  {/if}
</div>

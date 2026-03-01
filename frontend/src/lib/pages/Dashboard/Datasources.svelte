// FIXME: json file doesn't reload fine after clicking Save button
<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { user } from '../../stores/auth';
  import { get } from 'svelte/store';
  import { runningJobs, currentJobId } from '../../stores/downloads';
  import ConfirmDialog from '../../components/ConfirmDialog.svelte';
  import { openModal } from '../../stores/modal';
  import ConfigManager from '../../components/ConfigManager.svelte';
  import URLsManager from '../../components/URLsManager.svelte';
  import ManageMenuModal from '../../components/ManageMenuModal.svelte';
  import InputDialog from '../../components/InputDialog.svelte';
  import { showToast } from '../../stores/toasts';

  let configs: { name: string }[] = $state([]);
  let urls: { name: string }[] = $state([]);
  let downloadSources: { name: string }[] = $state([]);
  let selectedDatasource = $state('');
  let configContent = $state('');
  let urlContent = $state('');
  let loading = $state(false);
  let saving = $state(false);
  let error = $state('');
  let success = $state('');

  let downloadButtonState: 'idle' | 'downloading' | 'stopping' = $state('idle');

  let currentJob: any = $state(null);

  let configManager: ConfigManager;
  let urlsManager: URLsManager;

  let activeTab: 'urls' | 'config' = $state('urls');

  $effect(() => {
    if ($runningJobs.length > 0) {
      const myJob = $runningJobs.find(j => j.user_id === $user?.id);
      if (myJob) {
        currentJob = myJob;
        downloadButtonState = 'downloading';
      }
    } else if (downloadButtonState === 'downloading') {
      downloadButtonState = 'idle';
      currentJob = null;
    }
  });

  onMount(() => {
    loadData();
  });

  export async function loadData() {
    loading = true;
    try {
      const [configsRes, urlsRes, sourcesRes] = await Promise.all([
        api.getConfigs(),
        api.getUrls(),
        api.getDownloadSources()
      ]);
      configs = configsRes;
      urls = urlsRes;
      downloadSources = sourcesRes;
      
      if (configs.length > 0 && !selectedDatasource) {
        selectedDatasource = configs[0].name;
        await loadDatasourceContent(configs[0].name);
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  export async function selectDatasource(name: string) {
    selectedDatasource = name;
    await loadDatasourceContent(name);
  }

  export function getSelectedDatasource() {
    return selectedDatasource;
  }

  export function getDownloadButtonState() {
    return downloadButtonState;
  }

  export function setDownloadButtonState(state: 'idle' | 'downloading' | 'stopping') {
    downloadButtonState = state;
  }

  async function loadDatasourceContent(name: string) {
    loading = true;
    try {
      const [configRes, urlRes] = await Promise.all([
        api.getConfig(name),
        api.getUrlSource(name)
      ]);
      configContent = configRes.content;
      urlContent = urlRes.content;
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function handleConfigChange(event: CustomEvent) {
    configContent = JSON.stringify(event.detail, null, 2);
  }

  function handleUrlsChange(event: CustomEvent) {
    urlContent = JSON.stringify(event.detail, null, 2);
  }

  function fixConfigPaths(content: string, username: string): string {
    try {
      const parsed = JSON.parse(content);
      const fixedPath = `configs`;
      
      if (parsed['yt-dlp']) {
        if (parsed['yt-dlp']['--cookies']) {
          parsed['yt-dlp']['--cookies'] = `${fixedPath}/cookies.txt`;
        }
        if (parsed['yt-dlp']['--download-archive']) {
          parsed['yt-dlp']['--download-archive'] = `${fixedPath}/ytdl-archive.txt`;
        }
      }
      return JSON.stringify(parsed, null, 2);
    } catch {
      return content;
    }
  }

  async function saveConfig() {
    if (!selectedDatasource) return;
    saving = true;
    error = '';
    success = '';
    try {
      const currentUser = get(user);
      const fixedContent = fixConfigPaths(configContent, currentUser?.username || 'admin');
      await api.saveConfig(selectedDatasource, fixedContent);
      success = 'Config saved successfully';
      setTimeout(() => success = '', 3000);
    } catch (e: any) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  async function saveUrls() {
    if (!selectedDatasource) return;
    saving = true;
    error = '';
    success = '';
    try {
      await api.saveUrlSource(selectedDatasource, urlContent);
      success = 'URLs saved successfully';
      setTimeout(() => success = '', 3000);
    } catch (e: any) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  async function createNewDatasource() {
    openModal(InputDialog, {
      title: 'New Datasource',
      label: 'Name',
      placeholder: 'Enter datasource name',
      confirmText: 'Create',
      onSubmit: async (name: string) => {
        if (!name) return;
        
        if (configs.some(c => c.name === name)) {
          error = 'Datasource already exists';
          return;
        }

        saving = true;
        try {
          await api.saveConfig(name, '{"yt-dlp": {}, "custom": {}}');
          await api.saveUrlSource(name, '{}');
          await loadData();
          selectedDatasource = name;
          await loadDatasourceContent(name);
        } catch (e: any) {
          error = e.message;
        } finally {
          saving = false;
        }
      }
    });
  }

  async function renameDatasource() {
    if (!selectedDatasource) return;
    openModal(InputDialog, {
      title: 'Rename Datasource',
      label: 'New Name',
      value: selectedDatasource,
      placeholder: 'Enter new name',
      confirmText: 'Rename',
      onSubmit: async (newName: string) => {
        if (!newName || newName === selectedDatasource) return;
        
        if (configs.some(c => c.name === newName)) {
          error = 'Datasource name already exists';
          return;
        }

        saving = true;
        error = '';
        try {
          const [configRes, urlRes] = await Promise.all([
            api.getConfig(selectedDatasource),
            api.getUrlSource(selectedDatasource)
          ]);
          
          await api.saveConfig(newName, configRes.content);
          await api.saveUrlSource(newName, urlRes.content);
          await api.deleteConfig(selectedDatasource);
          await api.deleteUrlSource(selectedDatasource);
          
          selectedDatasource = newName;
          await loadData();
        } catch (e: any) {
          error = e.message;
        } finally {
          saving = false;
        }
      }
    });
  }

  async function deleteDatasource() {
    if (!selectedDatasource) return;
    openModal(ConfirmDialog, {
      title: 'Delete Datasource',
      message: `Are you sure you want to delete "${selectedDatasource}"? This action cannot be undone.`,
      confirmText: 'Delete',
      danger: true,
      onConfirm: async () => {
        try {
          await api.deleteConfig(selectedDatasource);
          await api.deleteUrlSource(selectedDatasource);
          selectedDatasource = '';
          configContent = '';
          urlContent = '';
          await loadData();
        } catch (e: any) {
          error = e.message;
        }
      }
    });
  }

  async function uploadCookies() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.txt';
    input.onchange = async (e) => {
      const file = (e.target as HTMLInputElement).files?.[0];
      if (!file) return;
      
      try {
        const result = await api.uploadCookies(file);
        showToast(result.message || 'Cookies uploaded successfully', 'success');
      } catch (e: any) {
        showToast(e.message || 'Failed to upload cookies', 'error');
      }
    };
    input.click();
  }

  async function resetArchive() {
    console.log('resetArchive function called, opening modal...');
    openModal(ConfirmDialog, {
      title: 'Reset Archive',
      message: 'This will delete your download archive file. Videos may be re-downloaded. Continue?',
      confirmText: 'Reset',
      danger: true,
      onConfirm: async () => {
        console.log('Confirm clicked, calling API');
        try {
          const result = await api.resetArchive();
          console.log('API result:', result);
          showToast(result.message || 'Archive reset successfully', 'success');
        } catch (e: any) {
          console.error('Reset archive error:', e);
          showToast(e.message || 'Failed to reset archive', 'error');
        }
      }
    });
    console.log('Modal should be open now');
  }

  async function startDownloadForAll() {
    if (downloadButtonState === 'downloading') {
      await stopDownload();
      return;
    }

    if (downloadButtonState === 'stopping') return;

    if (currentJob) {
      openModal(ConfirmDialog, {
        title: 'Stop Current Job',
        message: 'There is a running download job. Do you want to stop it and start a new one?',
        confirmText: 'Stop & Start',
        danger: true,
        onConfirm: async () => {
          await stopDownload();
          await doStartDownloadAll();
        }
      });
    } else {
      await doStartDownloadAll();
    }
  }

  async function doStartDownloadAll() {
    error = '';
    try {
      for (const source of downloadSources) {
        await api.startDownload(source.name);
      }
      downloadButtonState = 'downloading';
    } catch (e: any) {
      error = e.message;
    }
  }

  async function startDownload() {
    if (!selectedDatasource) return;

    if (currentJob) {
      openModal(ConfirmDialog, {
        title: 'Stop Current Job',
        message: 'There is a running download job. Do you want to stop it and start a new one?',
        confirmText: 'Stop & Start',
        danger: true,
        onConfirm: async () => {
          await stopDownload();
          await doStartDownload();
        }
      });
    } else {
      await doStartDownload();
    }
  }

  async function doStartDownload() {
    if (!selectedDatasource) return;
    error = '';
    try {
      const result = await api.startDownload(selectedDatasource);
      currentJobId.set(result.id);
      downloadButtonState = 'downloading';
    } catch (e: any) {
      error = e.message;
    }
  }

  async function stopDownload() {
    if (!currentJob) return;
    downloadButtonState = 'stopping';
    try {
      await api.stopJob(currentJob.id);
      downloadButtonState = 'idle';
      currentJob = null;
    } catch (e: any) {
      error = e.message;
    }
  }

  function toggleManageMenu() {
    openModal(ManageMenuModal, {
      onNewDatasource: createNewDatasource,
      onRename: renameDatasource,
      onDelete: deleteDatasource,
      onUploadCookies: uploadCookies,
      onResetArchive: resetArchive,
      hasSelection: !!selectedDatasource
    });
  }
</script>

<div class="grid grid-cols-1 md:grid-cols-4 gap-6">
  <div class="glass-card relative">
    <h3 class="text-lg font-semibold mb-4">Datasources</h3>
    
    <div class="flex flex-col gap-2 mb-4">
      <div class="flex gap-2">
        <button 
          class="glass-btn flex-1 text-sm !py-2"
          class:glass-btn-primary={downloadButtonState !== 'downloading'}
          class:glass-btn-danger={downloadButtonState === 'downloading'}
          onclick={startDownloadForAll}
          disabled={downloadButtonState === 'stopping'}
        >
          {#if downloadButtonState === 'downloading'}
            ⏹ Stop
          {:else}
            ⬇ Download
          {/if}
        </button>
        <button 
          class="glass-btn !py-2 !px-3 text-sm"
          onclick={toggleManageMenu}
        >
          ⚙ Manage
        </button>
      </div>
    </div>

    <div class="flex flex-col gap-2">
      {#each configs as cfg}
        <button 
          class="glass-btn w-full text-left {selectedDatasource === cfg.name ? 'glass-btn-selected' : ''}"
          onclick={() => selectDatasource(cfg.name)}
        >
          {cfg.name}
        </button>
      {/each}
    </div>
  </div>

  <div class="md:col-span-3 flex flex-col gap-4">
    {#if selectedDatasource}
      <div class="glass-card">
        <div class="tabs">
          <button 
            class="tab" 
            class:active={activeTab === 'urls'}
            onclick={() => activeTab = 'urls'}
          >
            URLs
          </button>
          <button 
            class="tab" 
            class:active={activeTab === 'config'}
            onclick={() => activeTab = 'config'}
          >
            Config
          </button>
        </div>

        {#if activeTab === 'urls'}
          <div class="tab-content">
            <URLsManager 
              bind:this={urlsManager}
              content={urlContent} 
              on:change={handleUrlsChange}
              onDownload={startDownload}
              isDownloading={downloadButtonState === 'downloading'}
              onStopDownload={stopDownload}
              onSave={saveUrls}
              saving={saving}
            />
          </div>
        {:else}
          <div class="tab-content">
            <ConfigManager 
              bind:this={configManager}
              content={configContent} 
              on:change={handleConfigChange}
              onSave={saveConfig}
              onSaved={() => loadDatasourceContent(selectedDatasource)}
              {saving}
            />
          </div>
        {/if}
      </div>
    {:else}
      <div class="glass-card text-center py-12 opacity-75">
        <p>Select or create a datasource to get started</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .dropdown-item {
    display: block;
    width: 100%;
    padding: 12px 16px;
    text-align: left;
    background: transparent;
    border: none;
    color: var(--text-primary, white);
    cursor: pointer;
    transition: background 0.15s;
  }

  .dropdown-item:hover {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  }

  .tabs {
    display: flex;
    gap: 4px;
    margin-bottom: 16px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
    padding-bottom: 8px;
  }

  .tab {
    padding: 10px 20px;
    background: transparent;
    border: none;
    border-radius: 6px 6px 0 0;
    color: #9ca3af;
    cursor: pointer;
    font-size: 14px;
    font-weight: 500;
    transition: all 0.15s;
    position: relative;
  }

  .tab:hover {
    color: #e5e7eb;
    background: rgba(255,255,255,0.05);
  }

  .tab.active {
    color: #60a5fa;
    background: rgba(59, 130, 246, 0.1);
  }

  .tab.active::after {
    content: '';
    position: absolute;
    bottom: -9px;
    left: 0;
    right: 0;
    height: 2px;
    background: #3b82f6;
  }

  .tab-content {
    padding-top: 8px;
  }

  .tab-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-bottom: 16px;
  }
</style>

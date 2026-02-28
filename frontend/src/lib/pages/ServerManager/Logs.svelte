<script lang="ts">
  import { onMount } from 'svelte';
  import LogViewer from '../../components/LogViewer.svelte';
  import { api } from '../../api/client';
  import SearchableSelect from '../../components/SearchableSelect.svelte';

  interface UserOption {
    value: string;
    label: string;
    isServer: boolean;
  }

  let users: UserOption[] = [];
  let selectedUser: string = '';
  let logContent: string = '';
  let loading = false;
  let error = '';
  let searchQuery = '';

  onMount(async () => {
    await loadUsers();
  });

  async function loadUsers() {
    try {
      const allUsers = await api.getUsers();
      users = [
        { value: 'server', label: 'Server (Backend)', isServer: true },
        ...allUsers.map((u: any) => ({ value: u.username, label: u.username, isServer: false }))
      ];
      if (users.length > 0) {
        selectedUser = 'server';
      }
    } catch (e: any) {
      error = e.message;
    }
  }

  async function loadLogs() {
    if (!selectedUser) return;
    
    loading = true;
    error = '';
    logContent = '';
    
    try {
      const userObj = users.find(u => u.value === selectedUser);
      if (userObj?.isServer) {
        logContent = await api.getServerLogs();
      } else {
        logContent = await api.getUserLogsByUsername(selectedUser);
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  $: if (selectedUser) {
    loadLogs();
  }

  $: selectOptions = users.map(u => ({ value: u.value, label: u.label }));
</script>

<div class="logs-page stagger-children">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-bold">Server Logs</h2>
    <button class="glass-btn" on:click={loadLogs} disabled={loading || !selectedUser}>
      {loading ? 'Loading...' : '🔄 Refresh'}
    </button>
  </div>

  <div class="glass-card mb-6">
    <div class="flex flex-wrap gap-4 items-end">
      <div class="flex-1 min-w-[250px]">
        <SearchableSelect
          label="Select Log Source:"
          options={selectOptions}
          bind:value={selectedUser}
          placeholder="Choose log source..."
        />
      </div>
    </div>
  </div>

  {#if error}
    <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
      <p class="text-red-300 text-sm">{error}</p>
    </div>
  {/if}

  <div class="glass-card">
    {#if loading}
      <div class="h-[500px] flex items-center justify-center opacity-75">
        Loading logs...
      </div>
    {:else if logContent}
      <LogViewer
        content={logContent}
        height="500px"
        lineNumbers={true}
        searchable={true}
        highlightWords={searchQuery ? [searchQuery] : []}
        theme="dark"
      />
    {:else}
      <div class="h-[500px] flex items-center justify-center opacity-75">
        No log content available
      </div>
    {/if}
  </div>
</div>

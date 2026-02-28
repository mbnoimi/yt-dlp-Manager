<script lang="ts">
  import Users from './ServerManager/Users.svelte';
  import Status from './ServerManager/Status.svelte';
  import Configs from './ServerManager/Configs.svelte';
  import Jobs from './ServerManager/Jobs.svelte';
  import Logs from './ServerManager/Logs.svelte';
  import Files from './ServerManager/Files.svelte';

  type TabName = 'users' | 'status' | 'configs' | 'jobs' | 'logs' | 'files';
  
  let activeTab: TabName = 'users';

  const tabs: { name: TabName; label: string; icon: string }[] = [
    { name: 'users', label: 'Users', icon: '👥' },
    { name: 'status', label: 'Status', icon: '📊' },
    { name: 'configs', label: 'Configs', icon: '⚙️' },
    { name: 'jobs', label: 'Jobs', icon: '📥' },
    { name: 'logs', label: 'Logs', icon: '📝' },
    { name: 'files', label: 'Files', icon: '📁' },
  ];
</script>

<div class="server-manager stagger-children">
  <div class="glass-tabs flex-wrap">
    {#each tabs as tab}
      <button 
        class="glass-tab {activeTab === tab.name ? 'active' : ''}"
        on:click={() => activeTab = tab.name}
      >
        <span class="mr-2">{tab.icon}</span>
        <span>{tab.label}</span>
      </button>
    {/each}
  </div>

  <div class="mt-6">
    {#if activeTab === 'users'}
      <Users />
    {:else if activeTab === 'status'}
      <Status />
    {:else if activeTab === 'configs'}
      <Configs />
    {:else if activeTab === 'jobs'}
      <Jobs />
    {:else if activeTab === 'logs'}
      <Logs />
    {:else if activeTab === 'files'}
      <Files />
    {/if}
  </div>
</div>

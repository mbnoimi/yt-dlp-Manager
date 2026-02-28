<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import LogViewer from '../../components/LogViewer.svelte';
  import { openModal } from '../../stores/modal';
  import ConfirmDialog from '../../components/ConfirmDialog.svelte';
  import { api } from '../../api/client';
  import { showToast } from '../../stores/toasts';
  import SearchableSelect from '../../components/SearchableSelect.svelte';

  interface UserJob {
    user_id: number;
    username: string;
    job_id: number;
    job_name: string;
    started_at: string | null;
  }

  let usersWithJobs: UserJob[] = [];
  let selectedUserId: string = '';
  let loading = false;
  let error = '';
  let eventSource: EventSource | null = null;
  let streamingLogs: string = '';
  let followLog = true;
  let searchQuery = '';

  let killingJob = false;
  let killingAll = false;

  onMount(async () => {
    await loadUsersWithJobs();
    startSSE();
  });

  onDestroy(() => {
    if (eventSource) {
      eventSource.close();
    }
  });

  async function loadUsersWithJobs() {
    loading = true;
    error = '';
    try {
      usersWithJobs = await api.getUsersWithJobs();
      if (usersWithJobs.length > 0 && !selectedUserId) {
        selectedUserId = String(usersWithJobs[0].user_id);
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function startSSE() {
    eventSource = api.createSSE();
    eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      updateStreamingLogs(data);
    };
    eventSource.onerror = () => {
      eventSource?.close();
      setTimeout(startSSE, 5000);
    };
  }

  function updateStreamingLogs(jobs: any[]) {
    const timestamp = new Date().toISOString();
    let logLines = '';
    
    if (jobs.length === 0) {
      logLines = `[${timestamp}] No running jobs\n`;
    } else {
      for (const job of jobs) {
        logLines += `[${timestamp}] Job #${job.id} - ${job.name} (User ID: ${job.user_id})\n`;
        if (job.current_url) {
          logLines += `  Current URL: ${job.current_url}\n`;
        }
      }
    }
    
    streamingLogs += logLines;
    
    const maxLines = 1000;
    const lines = streamingLogs.split('\n');
    if (lines.length > maxLines) {
      streamingLogs = lines.slice(-maxLines).join('\n');
    }
  }

  async function killSelectedJob(jobId: number) {
    console.log('Killing job:', jobId);
    killingJob = true;
    try {
      const result = await api.stopJob(jobId);
      console.log('Stop job result:', result);
      await loadUsersWithJobs();
    } catch (e: any) {
      console.error('Error killing job:', e);
      showToast(e.message, 'error');
    } finally {
      killingJob = false;
    }
  }

  async function killAllJobs() {
    console.log('Killing all jobs');
    killingAll = true;
    try {
      await api.stopAllJobs();
      await loadUsersWithJobs();
    } catch (e: any) {
      console.error('Error killing all jobs:', e);
      showToast(e.message, 'error');
    } finally {
      killingAll = false;
    }
  }

  $: selectedUser = usersWithJobs.find(u => String(u.user_id) === selectedUserId);
  $: jobSelectOptions = usersWithJobs.map(u => ({ 
    value: String(u.user_id), 
    label: `${u.username} - ${u.job_name}` 
  }));
</script>

<div class="jobs-page stagger-children">
  <div class="flex justify-between items-center mb-6">
    <h2 class="text-xl font-bold">Download Jobs</h2>
    <button class="glass-btn" on:click={loadUsersWithJobs} disabled={loading}>
      {loading ? 'Loading...' : '🔄 Refresh'}
    </button>
  </div>

  <div class="glass-card mb-6">
    <div class="flex flex-wrap gap-4 items-end">
      <div class="flex-1 min-w-[200px]">
        <SearchableSelect
          label="Select User with Running Job:"
          options={usersWithJobs.length > 0 ? jobSelectOptions : []}
          bind:value={selectedUserId}
          placeholder={usersWithJobs.length === 0 ? 'No running jobs' : 'Choose user...'}
        />
      </div>

      <div class="flex gap-3 mt-4">
        <button 
          class="glass-btn glass-btn-danger"
          disabled={!selectedUserId || usersWithJobs.length === 0}
          on:click={() => {
            const userJob = usersWithJobs.find(u => String(u.user_id) === selectedUserId);
            console.log('Selected userJob:', userJob);
            if (userJob) {
              openModal(ConfirmDialog, {
                title: 'Confirm Kill Job',
                message: `Are you sure you want to stop the job "${userJob.job_name}" for user "${userJob.username}"?`,
                confirmText: 'Kill',
                danger: true,
                onConfirm: () => {
                  console.log('Confirm clicked, calling killSelectedJob with:', userJob.job_id);
                  killSelectedJob(userJob.job_id);
                }
              });
            }
          }}
        >
          Kill Selected Job
        </button>
        <button 
          class="glass-btn glass-btn-danger"
          disabled={usersWithJobs.length === 0}
          on:click={() => {
            openModal(ConfirmDialog, {
              title: 'Confirm Kill All Jobs',
              message: `Are you sure you want to stop ALL running download jobs? This will affect ${usersWithJobs.length} job(s).`,
              confirmText: 'Kill All',
              danger: true,
              onConfirm: killAllJobs
            });
          }}
        >
          Kill All Jobs
        </button>
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
      <div class="h-[400px] flex items-center justify-center opacity-75">
        Loading...
      </div>
    {:else}
      <LogViewer
        content={streamingLogs}
        height="400px"
        lineNumbers={true}
        searchable={true}
        highlightWords={searchQuery ? [searchQuery] : []}
        theme="dark"
        follow={followLog}
      />
    {/if}
  </div>
</div>

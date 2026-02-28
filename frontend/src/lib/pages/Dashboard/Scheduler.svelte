<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { user } from '../../stores/auth';
  import ConfirmDialog from '../../components/ConfirmDialog.svelte';
  import { openModal } from '../../stores/modal';
  import { showToast } from '../../stores/toasts';
  import AddTaskModal from '../../components/AddTaskModal.svelte';

  interface ScheduledTask {
    id: number;
    user_id: number;
    name: string;
    task_type: string;
    datasource: string | null;
    cron_expression: string;
    config: string | null;
    is_active: boolean;
    last_run: string | null;
    next_run: string | null;
    created_at: string;
  }

  let tasks: ScheduledTask[] = $state([]);
  let downloadSources: { name: string }[] = $state([]);
  let users: any[] = $state([]);
  let loading = $state(false);
  let error = $state('');
  let isAdmin = $derived($user?.is_admin ?? false);

  export async function loadData() {
    loading = true;
    error = '';
    try {
      const [tasksRes, sourcesRes] = await Promise.all([
        isAdmin ? api.getAllScheduledTasks() : api.getScheduledTasks(),
        api.getDownloadSources()
      ]);
      tasks = tasksRes;
      downloadSources = sourcesRes;

      if (isAdmin) {
        users = await api.getUsers();
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    loadData();
  });

  function openCreate() {
    openModal(AddTaskModal, {
      task: null,
      downloadSources,
      users,
      isAdmin,
      onSave: loadData
    });
  }

  function openEdit(task: ScheduledTask) {
    openModal(AddTaskModal, {
      task,
      downloadSources,
      users,
      isAdmin,
      onSave: loadData
    });
  }

  async function deleteTask(task: ScheduledTask) {
    openModal(ConfirmDialog, {
      title: 'Delete Task',
      message: `Are you sure you want to delete "${task.name}"?`,
      confirmText: 'Delete',
      danger: true,
      onConfirm: async () => {
        try {
          await api.deleteScheduledTask(task.id);
          showToast('Task deleted successfully', 'success');
          await loadData();
        } catch (e: any) {
          showToast(e.message, 'error');
        }
      }
    });
  }

  async function toggleTask(task: ScheduledTask) {
    try {
      await api.updateScheduledTask(task.id, { is_active: !task.is_active });
      showToast(`Task ${task.is_active ? 'disabled' : 'enabled'} successfully`, 'success');
      await loadData();
    } catch (e: any) {
      showToast(e.message, 'error');
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString();
  }

  function getCronDescription(cron: string): string {
    const parts = cron.split(' ');
    if (parts.length !== 5) return cron;

    const [min, hour, day, month, dow] = parts;
    let desc = '';

    if (min === '0' && hour === '*' && day === '*' && month === '*' && dow === '*') {
      return 'Every hour';
    }
    if (min === '*' && hour === '*' && day === '*' && month === '*' && dow === '*') {
      return 'Every minute';
    }
    if (min !== '*' && hour !== '*' && day === '*' && month === '*' && dow === '*') {
      return `Daily at ${hour.padStart(2, '0')}:${min.padStart(2, '0')}`;
    }
    if (dow !== '*' && day === '*') {
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
      const dayNum = parseInt(dow);
      if (!isNaN(dayNum) && dayNum >= 0 && dayNum <= 6) {
        return `Every ${days[dayNum]} at ${hour.padStart(2, '0')}:${min.padStart(2, '0')}`;
      }
    }

    return cron;
  }

  function getUsername(userId: number): string {
    const u = users.find(u => u.id === userId);
    return u?.username || `User #${userId}`;
  }
</script>

<div class="scheduler-page">
  <div class="glass-card">
    <div class="flex justify-between items-center mb-6">
      <div>
        <h3 class="text-lg font-semibold">Scheduled Tasks</h3>
        <p class="text-sm opacity-75">Automate downloads and cleanup</p>
      </div>
      <button class="glass-btn glass-btn-primary" onclick={openCreate}>
        + New Task
      </button>
    </div>

    {#if error}
      <div class="!p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}

    {#if loading}
      <div class="text-center py-8 opacity-75">Loading tasks...</div>
    {:else if tasks.length === 0}
      <div class="text-center py-8 opacity-75">
        <p>No scheduled tasks yet</p>
        <p class="text-sm mt-2">Click "New Task" to create one</p>
      </div>
    {:else}
      <div class="tasks-grid">
        {#each tasks as task}
          <div class="task-card" class:inactive={!task.is_active}>
            <div class="task-header">
              <div class="task-info">
                <span class="task-type-badge" class:download={task.task_type === 'download'} class:cleanup={task.task_type === 'cleanup'}>
                  {task.task_type}
                </span>
                <h4 class="task-name">{task.name}</h4>
              </div>
              <label class="switch">
                <input type="checkbox" checked={task.is_active} onchange={() => toggleTask(task)} />
                <span class="slider"></span>
              </label>
            </div>

            <div class="task-details">
              <div class="detail-row">
                <span class="detail-label">Schedule:</span>
                <span class="detail-value">{getCronDescription(task.cron_expression)}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Cron:</span>
                <code class="detail-value cron">{task.cron_expression}</code>
              </div>
              {#if task.task_type === 'download'}
                <div class="detail-row">
                  <span class="detail-label">Datasource:</span>
                  <span class="detail-value">{task.datasource || '-'}</span>
                </div>
              {:else}
                <div class="detail-row">
                  <span class="detail-label">Config:</span>
                  <span class="detail-value">{task.config || '{days: 30}'}</span>
                </div>
              {/if}
              {#if isAdmin}
                <div class="detail-row">
                  <span class="detail-label">User:</span>
                  <span class="detail-value">{getUsername(task.user_id)}</span>
                </div>
              {/if}
              <div class="detail-row">
                <span class="detail-label">Last run:</span>
                <span class="detail-value">{formatDate(task.last_run)}</span>
              </div>
              <div class="detail-row">
                <span class="detail-label">Next run:</span>
                <span class="detail-value">{formatDate(task.next_run)}</span>
              </div>
            </div>

            <div class="task-actions">
              <button class="glass-btn !py-1 !px-2 text-sm" onclick={() => openEdit(task)}>
                ✏️ Edit
              </button>
              <button class="glass-btn !py-1 !px-2 text-sm danger" onclick={() => deleteTask(task)}>
                🗑️ Delete
              </button>
            </div>
          </div>
        {/each}
      </div>
    {/if}
  </div>
</div>

<style>
  .scheduler-page {
    width: 100%;
  }

  .tasks-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 16px;
  }

  .task-card {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    padding: 16px;
    transition: all 0.2s;
  }

  .task-card.inactive {
    opacity: 0.6;
  }

  .task-card:hover {
    border-color: rgba(255, 255, 255, 0.2);
  }

  .task-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 12px;
  }

  .task-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .task-type-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
  }

  .task-type-badge.download {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
  }

  .task-type-badge.cleanup {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
  }

  .task-name {
    font-size: 15px;
    font-weight: 600;
    margin: 0;
  }

  .task-details {
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }

  .detail-row {
    display: flex;
    gap: 8px;
    font-size: 13px;
  }

  .detail-label {
    color: #9ca3af;
    min-width: 80px;
  }

  .detail-value {
    color: #e5e7eb;
  }

  .detail-value.cron {
    font-family: monospace;
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .task-actions {
    display: flex;
    gap: 8px;
    padding-top: 12px;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
  }

  .task-actions .danger {
    color: #f87171;
  }

  .switch {
    position: relative;
    display: inline-block;
    width: 36px;
    height: 20px;
  }

  .switch input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(255, 255, 255, 0.1);
    transition: 0.2s;
    border-radius: 20px;
  }

  .slider:before {
    position: absolute;
    content: "";
    height: 14px;
    width: 14px;
    left: 3px;
    bottom: 3px;
    background-color: white;
    transition: 0.2s;
    border-radius: 50%;
  }

  input:checked + .slider {
    background-color: #3b82f6;
  }

  input:checked + .slider:before {
    transform: translateX(16px);
  }
</style>

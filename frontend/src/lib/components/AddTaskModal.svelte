<script lang="ts">
  import { closeModal } from '../stores/modal';
  import { api } from '../api/client';
  import { showToast } from '../stores/toasts';

  let { task = null, downloadSources = [], users = [], isAdmin = false, onSave } = $props<{
    task?: any;
    downloadSources?: { name: string }[];
    users?: any[];
    isAdmin?: boolean;
    onSave?: () => void;
  }>();

  let name = $state(task?.name || '');
  let task_type = $state(task?.task_type || 'download');
  let datasource = $state(task?.datasource || '');
  let cron_expression = $state(task?.cron_expression || '0 2 * * *');
  let config = $state(task?.config || '');
  let target_user_id = $state<number | undefined>(undefined);
  let saving = $state(false);
  let error = $state('');

  let isEditing = $derived(!!task);

  const cronTemplates = [
    { label: 'Every minute', value: '* * * * *' },
    { label: 'Every hour', value: '0 * * * *' },
    { label: 'Daily at midnight', value: '0 0 * * *' },
    { label: 'Daily at 2am', value: '0 2 * * *' },
    { label: 'Daily at 6am', value: '0 6 * * *' },
    { label: 'Weekly (Sunday)', value: '0 0 * * 0' },
    { label: 'Weekly (Monday)', value: '0 0 * * 1' },
    { label: 'Monthly (1st)', value: '0 0 1 * *' },
    { label: 'Manual', value: '' }
  ];

  let useCronTemplate = $state(true);
  let selectedTemplate = $state('0 2 * * *');

  function handleTemplateChange(e: Event) {
    const target = e.target as HTMLSelectElement;
    const value = target.value;
    if (value) {
      selectedTemplate = value;
      cron_expression = value;
      useCronTemplate = true;
    } else {
      useCronTemplate = false;
    }
  }

  function handleConfigInput(e: Event) {
    const target = e.target as HTMLInputElement;
    target.value = target.value.replace(/\D/g, '');
    config = target.value ? `{"days": ${parseInt(target.value) || 30}}` : '';
  }

  async function save() {
    if (!name || !cron_expression) {
      error = 'Please fill in required fields';
      return;
    }

    saving = true;
    error = '';

    try {
      const payload: any = {
        name,
        task_type,
        cron_expression
      };

      if (task_type === 'download') {
        payload.datasource = datasource;
      } else if (task_type === 'cleanup') {
        payload.config = config || '{"days": 30}';
      }

      if (isAdmin && target_user_id) {
        payload.target_user_id = target_user_id;
      }

      if (isEditing) {
        await api.updateScheduledTask(task.id, payload);
        showToast('Task updated successfully', 'success');
      } else {
        await api.createScheduledTask(payload);
        showToast('Task created successfully', 'success');
      }
      closeModal();
      if (onSave) onSave();
    } catch (e: any) {
      error = e.message || 'Failed to save task';
    } finally {
      saving = false;
    }
  }

  function handleClose() {
    closeModal();
  }
</script>

<div class="glass-modal-overlay" onclick={handleClose} onkeydown={(e) => e.key === 'Escape' && handleClose()} role="dialog" aria-modal="true">
  <div class="glass-modal animate-scaleIn" onclick={(e) => e.stopPropagation()} onkeydown={(e) => e.stopPropagation()} role="document">
    <h3 class="text-lg font-bold mb-4">{isEditing ? 'Edit Task' : 'New Task'}</h3>
    
    {#if error}
      <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}
    
    <div class="space-y-4">
      <div>
        <label class="block text-sm mb-1">Task Name</label>
        <input 
          type="text" 
          bind:value={name} 
          class="glass-input w-full"
          placeholder="e.g., Daily backup"
        />
      </div>

      <div>
        <label class="block text-sm mb-1">Task Type</label>
        <select 
          bind:value={task_type} 
          class="glass-input w-full"
        >
          <option value="download">Download</option>
          <option value="cleanup">Cleanup</option>
        </select>
      </div>

      {#if task_type === 'download'}
        <div>
          <label class="block text-sm mb-1">Datasource</label>
          <select 
            bind:value={datasource} 
            class="glass-input w-full"
          >
            <option value="">Select datasource...</option>
            {#each downloadSources as source}
              <option value={source.name}>{source.name}</option>
            {/each}
          </select>
        </div>
      {:else}
        <div>
          <label class="block text-sm mb-1">Days to keep</label>
          <input 
            type="text" 
            oninput={handleConfigInput}
            class="glass-input w-full font-mono"
            placeholder="30"
          />
        </div>
      {/if}

      <div>
        <label class="block text-sm mb-1">Cron Expression</label>
        <select 
          onchange={handleTemplateChange}
          class="glass-input w-full mb-2"
        >
          {#each cronTemplates as template}
            <option value={template.value} selected={cron_expression === template.value && useCronTemplate}>
              {template.label} ({template.value || 'manual'})
            </option>
          {/each}
        </select>
        <input 
          type="text" 
          bind:value={cron_expression} 
          class="glass-input w-full font-mono"
          placeholder="0 2 * * *"
        />
        <p class="text-xs opacity-75 mt-1">
          Format: minute hour day month weekday
        </p>
      </div>

      {#if isAdmin}
        <div>
          <label class="block text-sm mb-1">Target User (optional)</label>
          <select 
            bind:value={target_user_id} 
            class="glass-input w-full"
          >
            <option value={undefined}>Current user</option>
            {#each users as u}
              <option value={u.id}>{u.username}</option>
            {/each}
          </select>
        </div>
      {/if}
    </div>
    
    <div class="flex justify-end gap-3 mt-6">
      <button class="glass-btn" onclick={handleClose}>
        Cancel
      </button>
      <button class="glass-btn" onclick={save} disabled={saving || !name || !cron_expression}>
        {saving ? 'Saving...' : (isEditing ? 'Update' : 'Create')}
      </button>
    </div>
  </div>
</div>

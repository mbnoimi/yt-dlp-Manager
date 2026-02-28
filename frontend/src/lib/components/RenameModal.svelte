<script lang="ts">
  import { closeModal } from '../stores/modal';

  export let title: string = 'Rename';
  export let currentName: string = '';
  export let onRename: ((newName: string) => Promise<void>) | undefined = undefined;

  let newName = currentName;
  let saving = false;
  let error = '';

  async function handleRename() {
    if (!newName || newName === currentName) return;
    saving = true;
    error = '';

    try {
      if (onRename) {
        await onRename(newName);
      }
      closeModal();
    } catch (e: any) {
      error = e.message || 'Failed to rename';
    } finally {
      saving = false;
    }
  }

  function handleClose() {
    closeModal();
  }
</script>

<div class="glass-modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()}>
  <div class="glass-modal animate-scaleIn" on:click|stopPropagation on:keydown|stopPropagation>
    <div class="flex justify-between items-start mb-4">
      <h3 class="font-bold text-lg">{title}</h3>
      <button class="glass-btn !p-1 opacity-50 hover:opacity-100" on:click={handleClose}>
        ✕
      </button>
    </div>
    
    <div class="mb-4">
      <label for="newName" class="block mb-2">New Name</label>
      <input type="text" id="newName" bind:value={newName} class="glass-input" />
    </div>

    {#if error}
      <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}

    <div class="flex gap-3 justify-end">
      <button class="glass-btn" on:click={handleClose}>
        Cancel
      </button>
      <button class="glass-btn glass-btn-primary" on:click={handleRename} disabled={saving || !newName || newName === currentName}>
        {saving ? 'Renaming...' : 'Rename'}
      </button>
    </div>
  </div>
</div>

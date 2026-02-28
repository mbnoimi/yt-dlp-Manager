<script lang="ts">
  import Modal from './Modal.svelte';
  import { closeModal } from '../stores/modal';

  export let onAdd: (name: string) => void;

  let newFolderName = '';
  let error = '';

  function handleAdd() {
    if (!newFolderName.trim()) {
      error = 'Please enter a path name';
      return;
    }
    onAdd(newFolderName.trim());
    newFolderName = '';
    closeModal();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter') handleAdd();
  }

  function handleCancel() {
    newFolderName = '';
    closeModal();
  }
</script>

<Modal title="Add Path">
  <input
    type="text"
    class="glass-input w-full"
    placeholder="Path name (e.g., My Videos/subfolder)"
    bind:value={newFolderName}
    onkeydown={handleKeydown}
  />
  
  {#if error}
    <p class="text-red-400 text-sm mt-2">{error}</p>
  {/if}
  
  <div class="flex gap-3 mt-4">
    <button class="glass-btn flex-1" onclick={handleCancel}>
      Cancel
    </button>
    <button class="glass-btn glass-btn-primary flex-1" onclick={handleAdd}>
      Add
    </button>
  </div>
</Modal>

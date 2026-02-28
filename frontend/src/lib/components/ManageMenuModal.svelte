<script lang="ts">
  import Modal from './Modal.svelte';
  import { closeModal } from '../stores/modal';

  export let onNewDatasource: () => void;
  export let onRename: (() => void) | null = null;
  export let onDelete: (() => void) | null = null;
  export let onUploadCookies: () => void;
  export let onResetArchive: () => void;
  export let hasSelection: boolean = false;

  function handleNewDatasource() {
    closeModal();
    onNewDatasource();
  }

  function handleRename() {
    closeModal();
    onRename?.();
  }

  function handleDelete() {
    closeModal();
    onDelete?.();
  }

  function handleUploadCookies() {
    closeModal();
    onUploadCookies();
  }

  function handleResetArchive() {
    closeModal();
    console.log('Reset Archive clicked');
    onResetArchive();
  }
</script>

<Modal title="⚙️ Datasource Manager">
  <div class="menu-content">
    <button class="dropdown-item w-full text-left" on:click={handleNewDatasource}>
      <span class="item-icon">➕</span>
      <span>New</span>
    </button>

    {#if hasSelection}
      <button class="dropdown-item w-full text-left" on:click={handleRename}>
        <span class="item-icon">✏️</span>
        <span>Rename</span>
      </button>
      <button class="dropdown-item w-full text-left danger" on:click={handleDelete}>
        <span class="item-icon">🗑️</span>
        <span>Delete</span>
      </button>
    {/if}

    <button class="dropdown-item w-full text-left" on:click={handleUploadCookies}>
      <span class="item-icon">📤</span>
      <span>Upload cookies</span>
    </button>
    <button class="dropdown-item w-full text-left danger" on:click={handleResetArchive}>
      <span class="item-icon">♻️</span>
      <span>Reset Archive</span>
    </button>
  </div>
</Modal>

<style>
  .menu-content {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .dropdown-item {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    width: 100%;
    padding: 12px 16px;
    text-align: left;
    background: transparent;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: all 0.15s;
    border-radius: 8px;
    font-size: 0.95rem;
  }

  .dropdown-item:hover {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  }

  .dropdown-item.danger:hover {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.3) 100%);
  }

  .item-icon {
    font-size: 1.1rem;
    width: 1.5rem;
    text-align: center;
  }
</style>

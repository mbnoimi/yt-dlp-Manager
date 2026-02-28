<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { closeModal } from '../stores/modal';

  export let title: string = '';
  export let message: string = '';
  export let confirmText: string = 'Confirm';
  export let danger: boolean = false;
  export let onConfirm: (() => void) | undefined = undefined;

  const dispatch = createEventDispatcher();

  function handleCancel() {
    dispatch('cancel');
    closeModal();
  }

  function handleConfirm() {
    if (onConfirm) {
      onConfirm();
    }
    dispatch('confirm');
    closeModal();
  }
</script>

<div class="glass-modal-overlay" on:click={handleCancel} on:keydown={(e) => e.key === 'Escape' && handleCancel()}>
  <div class="glass-modal animate-scaleIn" on:click|stopPropagation on:keydown|stopPropagation>
    {#if title}
      <h3 class="font-bold text-lg mb-4" class:text-red-400={danger}>{title}</h3>
    {/if}
    {#if message}
      <p class="opacity-75 mb-6">{message}</p>
    {/if}
    <div class="flex gap-3 justify-end">
      <button class="glass-btn" on:click={handleCancel}>
        Cancel
      </button>
      <button 
        class="glass-btn" 
        class:glass-btn-danger={danger}
        class:glass-btn-primary={!danger}
        on:click={handleConfirm}
      >
        {confirmText}
      </button>
    </div>
  </div>
</div>

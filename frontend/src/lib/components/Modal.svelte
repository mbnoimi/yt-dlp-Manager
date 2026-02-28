<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { closeModal } from '../stores/modal';

  export let title: string = '';
  export let showClose: boolean = true;

  const dispatch = createEventDispatcher();

  function handleClose() {
    closeModal();
    dispatch('close');
  }
</script>

<div class="glass-modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()}>
  <div class="glass-modal animate-scaleIn" on:click|stopPropagation on:keydown|stopPropagation>
    {#if title || showClose}
      <div class="flex justify-between items-start mb-4">
        {#if title}
          <h3 class="font-bold text-lg">{title}</h3>
        {/if}
        {#if showClose}
          <button class="glass-btn !p-1 opacity-50 hover:opacity-100" on:click={handleClose}>
            ✕
          </button>
        {/if}
      </div>
    {/if}
    <slot />
  </div>
</div>

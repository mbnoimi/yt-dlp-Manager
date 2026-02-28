<script lang="ts">
  import { closeModal } from '../stores/modal';

  export let title: string = 'Enter Value';
  export let label: string = 'Name';
  export let value: string = '';
  export let placeholder: string = '';
  export let confirmText: string = 'Confirm';
  export let onSubmit: ((value: string) => void) | null = null;

  function handleSubmit() {
    closeModal();
    onSubmit?.(value);
  }

  function handleCancel() {
    closeModal();
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      handleCancel();
    }
  }
</script>

<div class="glass-modal-overlay" on:click={handleCancel} on:keydown={handleKeydown}>
  <div class="glass-modal animate-scaleIn w-80" on:click|stopPropagation on:keydown|stopPropagation>
    <h3 class="font-bold text-lg mb-4">{title}</h3>
    
    <div class="mb-4">
      <label class="block text-sm opacity-75 mb-2">{label}</label>
      <input
        type="text"
        class="glass-input w-full"
        bind:value={value}
        {placeholder}
        on:keydown={(e) => e.key === 'Enter' && handleSubmit()}
        autofocus
      />
    </div>

    <div class="flex gap-3 justify-end">
      <button class="glass-btn" on:click={handleCancel}>
        Cancel
      </button>
      <button class="glass-btn glass-btn-primary" on:click={handleSubmit}>
        {confirmText}
      </button>
    </div>
  </div>
</div>
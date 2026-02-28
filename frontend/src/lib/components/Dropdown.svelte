<script lang="ts">
  import { dropdownOutlet, closeModal } from '../stores/modal';

  let search = '';
  let inputRef: HTMLInputElement;

  $: filteredOptions = $dropdownOutlet?.options.filter(opt => 
    opt.label.toLowerCase().includes(search.toLowerCase())
  ) ?? [];

  function selectOption(opt: { value: string; label: string }) {
    if ($dropdownOutlet) {
      $dropdownOutlet.onSelect(opt);
    }
    closeDropdown();
  }

  function closeDropdown() {
    search = '';
    dropdownOutlet.set(null);
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') {
      closeDropdown();
    }
  }

  $: if ($dropdownOutlet && inputRef) {
    search = '';
    setTimeout(() => inputRef?.focus(), 0);
  }
</script>

{#if $dropdownOutlet}
  <div class="glass-modal-overlay" on:click={closeDropdown} on:keydown={handleKeydown}>
    <div class="glass-modal animate-scaleIn" on:click|stopPropagation on:keydown|stopPropagation>
      {#if $dropdownOutlet.searchable && $dropdownOutlet.options.length > 0}
        <input
          type="text"
          bind:this={inputRef}
          bind:value={search}
          placeholder="Search..."
          class="glass-input !rounded-b-none !border-b-0"
          on:keydown={handleKeydown}
        />
      {/if}
      <div class="max-h-60 overflow-y-auto">
        {#each filteredOptions as opt}
          <button
            type="button"
            class="dropdown-item"
            class:active={opt.value === $dropdownOutlet?.value}
            on:click={() => selectOption(opt)}
          >
            {opt.label}
          </button>
        {:else}
          <div class="p-3 text-center opacity-50">No results</div>
        {/each}
      </div>
    </div>
  </div>
{/if}

<style>
  .dropdown-item {
    display: block;
    width: 100%;
    padding: 12px 16px;
    text-align: left;
    background: transparent;
    border: none;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.15s;
  }

  .dropdown-item:hover,
  .dropdown-item.active {
    background: linear-gradient(90deg, rgba(59, 130, 246, 0.3) 0%, rgba(139, 92, 246, 0.3) 100%);
  }
</style>

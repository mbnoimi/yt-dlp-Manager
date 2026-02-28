<script lang="ts">
  import { openDropdown } from '../stores/modal';

  export let options: { value: string; label: string }[] = [];
  export let value: string = '';
  export let placeholder: string = 'Select...';
  export let label: string = '';
  export let searchable: boolean = true;

  $: selectedLabel = options.find(o => o.value === value)?.label || '';

  function toggle() {
    openDropdown({
      options,
      value,
      searchable,
      onSelect: (opt) => {
        value = opt.value;
      }
    });
  }
</script>

<div class="searchable-select">
  {#if label}
    <label class="block mb-2 text-sm opacity-75">{label}</label>
  {/if}
  
  <button
    type="button"
    class="glass-input text-left flex items-center justify-between"
    on:click={toggle}
  >
    <span class:opacity-50={!value}>{selectedLabel || placeholder}</span>
    <span class="pointer-events-none">▼</span>
  </button>
</div>

<style>
  .searchable-select {
    width: 100%;
  }
</style>

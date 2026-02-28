<script lang="ts">
  import { onMount, createEventDispatcher } from 'svelte';
  import { openModal } from '../stores/modal';
  import AddPathModal from './AddPathModal.svelte';

  interface Props {
    content?: string;
    disabled?: boolean;
    onDownload?: () => void;
    isDownloading?: boolean;
    onStopDownload?: () => void;
    onSave?: () => void;
    saving?: boolean;
  }

  let { content = '', disabled = false, onDownload, isDownloading = false, onStopDownload, onSave, saving = false }: Props = $props();

  const dispatch = createEventDispatcher();

  interface FolderEntry {
    name: string;
    urls: string[];
    isArray: boolean;
  }

  let folders: FolderEntry[] = $state([]);
  let newUrl = $state('');
  let editingIndex = $state(-1);
  let filterText = $state('');

  let filteredFolders = $derived(
    filterText.trim() 
      ? folders.filter(f => f.name.toLowerCase().includes(filterText.toLowerCase()))
      : folders
  );

  function parseContent() {
    let parsed: any = {};
    try {
      parsed = JSON.parse(content);
    } catch (e) {
      parsed = {};
    }

    folders = Object.entries(parsed).map(([name, value]) => ({
      name,
      urls: Array.isArray(value) ? value : [value as string],
      isArray: Array.isArray(value)
    }));
  }

  function emitChange() {
    const result: Record<string, string | string[]> = {};
    
    folders.forEach(folder => {
      if (folder.urls.length === 1 && !folder.isArray) {
        result[folder.name] = folder.urls[0];
      } else {
        result[folder.name] = folder.urls.filter(u => u.trim());
      }
    });

    dispatch('change', result);
  }

  function removeFolder(index: number) {
    folders = folders.filter((_, i) => i !== index);
    emitChange();
  }

  function addUrlToFolder(index: number) {
    folders[index].urls = [...folders[index].urls, ''];
    folders = [...folders];
  }

  function removeUrlFromFolder(folderIndex: number, urlIndex: number) {
    folders[folderIndex].urls = folders[folderIndex].urls.filter((_, i) => i !== urlIndex);
    folders = [...folders];
    emitChange();
  }

  function updateUrl(folderIndex: number, urlIndex: number, value: string) {
    folders[folderIndex].urls[urlIndex] = value;
    folders = [...folders];
    emitChange();
  }

  function toggleArrayMode(index: number) {
    folders[index].isArray = !folders[index].isArray;
    if (folders[index].isArray && folders[index].urls.length === 1) {
      folders[index].urls = [folders[index].urls[0], ''];
    }
    folders = [...folders];
    emitChange();
  }

  function handleAddPath(name: string) {
    if (!folders.find(f => f.name === name)) {
      folders = [{ name, urls: [''], isArray: false }, ...folders];
      emitChange();
    }
  }

  function showAddPathModal() {
    openModal(AddPathModal, {
      onAdd: handleAddPath
    });
  }

  $effect(() => {
    parseContent();
  });

  export function getContent(): string {
    return content;
  }

  export function setContent(newContent: string) {
    content = newContent;
    parseContent();
  }

  onMount(() => {
    parseContent();
  });
</script>

<div class="urls-editor">
  <div class="header">
    <div class="header-left">
      {#if onSave}
        <button class="save-btn" onclick={onSave} disabled={saving}>
          💾 {saving ? 'Saving...' : 'Save'}
        </button>
      {/if}
      {#if isDownloading}
        <button class="download-btn danger" onclick={onStopDownload} {disabled}>
          ⏹ Stop
        </button>
      {:else if onDownload}
        <button class="download-btn" onclick={onDownload} {disabled}>
          ▶ Download Datasource
        </button>
      {/if}
    </div>
    <div class="header-right">
      <input
        type="text"
        class="filter-input"
        placeholder="Filter paths..."
        bind:value={filterText}
      />
      <button class="add-folder-btn" onclick={showAddPathModal} {disabled}>
        ➕ Add Path
      </button>
    </div>
  </div>

  <div class="folders-list">
      {#each filteredFolders as folder, index}
      <div class="folder-card">
        <div class="folder-header">
          <div class="folder-name-wrapper">
            <span class="folder-icon">📁</span>
            <input
              type="text"
              class="folder-name-input"
              bind:value={folder.name}
              oninput={() => emitChange()}
              {disabled}
            />
          </div>
          <div class="folder-actions">
            <button 
              class="mode-toggle" 
              onclick={() => toggleArrayMode(index)}
              title={folder.isArray ? 'Switch to single URL' : 'Switch to multiple URLs'}
              {disabled}
            >
              {folder.isArray ? '📋 Multiple' : '🔗 Single'}
            </button>
            <button class="remove-folder-btn" onclick={() => removeFolder(index)} {disabled}>×</button>
          </div>
        </div>

        <div class="urls-container">
          {#each folder.urls as url, urlIndex}
            <div class="url-row">
              <input
                type="url"
                class="url-input"
                placeholder="https://youtube.com/..."
                value={url}
                oninput={(e) => updateUrl(index, urlIndex, e.currentTarget.value)}
                {disabled}
              />
              {#if folder.isArray || folder.urls.length > 1}
                <button 
                  class="remove-url-btn" 
                  onclick={() => removeUrlFromFolder(index, urlIndex)}
                  disabled={disabled || (folder.urls.length === 1 && !folder.isArray)}
                >
                  ×
                </button>
              {/if}
            </div>
          {/each}
          
          {#if folder.isArray}
            <button class="add-url-btn" onclick={() => addUrlToFolder(index)} {disabled}>
              + Add URL
            </button>
          {/if}
        </div>
      </div>
    {/each}

    {#if folders.length === 0}
      <div class="empty-state">
        <p>No paths configured.</p>
        <p class="sub">Click "+ Add Path" to create your first path.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .urls-editor {
    width: 100%;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
  }

  .header-left, .header-right {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .filter-input {
    padding: 8px 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: white;
    font-size: 13px;
    width: 180px;
  }

  .filter-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .filter-input::placeholder {
    color: #6b7280;
  }

  .save-btn {
    font-size: 14px;
    padding: 10px 20px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .save-btn:hover:not(:disabled) {
    background: #2563eb;
  }

  .save-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .download-btn {
    font-size: 14px;
    padding: 10px 20px;
    background: #10b981;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .download-btn:hover:not(:disabled) {
    background: #059669;
  }

  .download-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .download-btn.danger {
    background: #ef4444;
  }

  .download-btn.danger:hover:not(:disabled) {
    background: #dc2626;
  }

  .add-folder-btn {
    font-size: 14px;
    padding: 10px 20px;
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 6px;
    cursor: pointer;
    transition: background 0.15s;
  }

  .add-folder-btn:hover:not(:disabled) {
    background: #2563eb;
  }

  .add-folder-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .folders-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .folder-card {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 8px;
    padding: 16px;
  }

  .folder-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 12px;
    border-bottom: 1px solid rgba(255,255,255,0.1);
  }

  .folder-name-wrapper {
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
  }

  .folder-icon {
    font-size: 18px;
  }

  .folder-name-input {
    flex: 1;
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #a78bfa;
    font-size: 14px;
    font-weight: 500;
  }

  .folder-name-input:focus {
    outline: none;
    border-color: #8b5cf6;
  }

  .folder-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .mode-toggle {
    font-size: 11px;
    padding: 4px 8px;
    background: rgba(139, 92, 246, 0.2);
    border: 1px solid rgba(139, 92, 246, 0.3);
    border-radius: 4px;
    color: #a78bfa;
    cursor: pointer;
    transition: all 0.15s;
  }

  .mode-toggle:hover:not(:disabled) {
    background: rgba(139, 92, 246, 0.3);
  }

  .mode-toggle:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .remove-folder-btn {
    width: 28px;
    height: 28px;
    background: rgba(239, 68, 68, 0.2);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 4px;
    color: #f87171;
    cursor: pointer;
    font-size: 18px;
    line-height: 1;
    transition: all 0.15s;
  }

  .remove-folder-btn:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.4);
  }

  .remove-folder-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .urls-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .url-row {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .url-input {
    flex: 1;
    padding: 8px 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 4px;
    color: #60a5fa;
    font-size: 13px;
    font-family: monospace;
  }

  .url-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .url-input:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .remove-url-btn {
    width: 28px;
    height: 28px;
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.2);
    border-radius: 4px;
    color: #f87171;
    cursor: pointer;
    font-size: 16px;
    transition: all 0.15s;
  }

  .remove-url-btn:hover:not(:disabled) {
    background: rgba(239, 68, 68, 0.2);
  }

  .remove-url-btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
  }

  .add-url-btn {
    align-self: flex-start;
    font-size: 12px;
    padding: 6px 12px;
    background: transparent;
    border: 1px dashed rgba(255,255,255,0.2);
    border-radius: 4px;
    color: #6b7280;
    cursor: pointer;
    transition: all 0.15s;
  }

  .add-url-btn:hover:not(:disabled) {
    border-color: #3b82f6;
    color: #3b82f6;
  }

  .add-url-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .empty-state {
    text-align: center;
    padding: 40px;
    color: #6b7280;
  }

  .empty-state .sub {
    font-size: 12px;
    margin-top: 8px;
  }

  .modal-input {
    width: 100%;
    padding: 12px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    color: white;
    font-size: 14px;
    box-sizing: border-box;
  }

  .modal-input:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .modal-actions {
    display: flex;
    gap: 12px;
    margin-top: 16px;
  }

  .cancel-btn {
    flex: 1;
    padding: 10px;
    background: rgba(255,255,255,0.1);
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
  }

  .confirm-btn {
    flex: 1;
    padding: 10px;
    background: #3b82f6;
    border: none;
    border-radius: 6px;
    color: white;
    cursor: pointer;
  }

  .confirm-btn:hover {
    background: #2563eb;
  }
</style>

<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../api/client';
  import RenameModal from '../components/RenameModal.svelte';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';
  import { openModal } from '../stores/modal';

  interface FileItem {
    name: string;
    path: string;
    is_dir: boolean;
    size: number;
    modified?: string;
  }

  let {
    mode = 'user',
    title = 'Files',
    basePath = '',
    rootLabel = 'Root'
  } = $props();

  const PAGE_SIZE = 50;

  let currentPath: string = $state('');
  let files: FileItem[] = $state([]);
  let loading = $state(false);
  let loadingMore = $state(false);
  let error = $state('');
  let selectedFile: FileItem | null = $state(null);
  let hasMore = $state(false);
  let total = $state(0);

  let pathHistory: string[] = $state([]);
  let breadcrumbs: string[] = $state([]);

  onMount(async () => {
    await loadFiles('');
  });

  export async function refresh() {
    await loadFiles(currentPath);
  }

  async function loadFiles(path: string, append: boolean = false) {
    if (append) {
      loadingMore = true;
    } else {
      loading = true;
      files = [];
    }
    error = '';
    try {
      let result: any;
      
      if (mode === 'admin') {
        result = await api.getAdminFiles(path, append ? files.length : 0, PAGE_SIZE);
        const newFiles = result.files.map((f: any) => ({
          name: f.path.split('/').pop() || f.path,
          path: f.path,
          is_dir: f.is_dir,
          size: f.size,
          modified: f.modified
        }));
        
        newFiles.sort((a: FileItem, b: FileItem) => {
          if (a.is_dir && !b.is_dir) return -1;
          if (!a.is_dir && b.is_dir) return 1;
          return a.name.localeCompare(b.name);
        });
        
        files = append ? [...files, ...newFiles] : newFiles;
        hasMore = result.has_more;
        total = result.total;
      } else {
        const userFiles = await api.getFiles(path);
        const allFiles: FileItem[] = userFiles.map((f: any) => ({
          name: f.path.split('/').pop() || f.path,
          path: f.path,
          is_dir: f.is_dir,
          size: f.size
        }));
        
        allFiles.sort((a, b) => {
          if (a.is_dir && !b.is_dir) return -1;
          if (!a.is_dir && b.is_dir) return 1;
          return a.name.localeCompare(b.name);
        });
        
        files = allFiles;
        hasMore = false;
        total = files.length;
      }
      
      currentPath = path;
    } catch (e: any) {
      error = e.message || 'Failed to load files';
    } finally {
      loading = false;
      loadingMore = false;
    }
  }

  async function loadMore() {
    if (loadingMore || !hasMore) return;
    await loadFiles(currentPath, true);
  }

  function navigateToFolder(folderName: string) {
    const newPath = currentPath ? `${currentPath}/${folderName}` : folderName;
    pathHistory = [...pathHistory, currentPath];
    loadFiles(newPath);
    updateBreadcrumbs(newPath);
  }

  function navigateBack() {
    if (pathHistory.length > 0) {
      const prevPath = pathHistory.pop();
      loadFiles(prevPath || '');
      updateBreadcrumbs(prevPath || '');
    }
  }

  function updateBreadcrumbs(path: string) {
    breadcrumbs = path ? path.split('/') : [];
  }

  function goToBreadcrumb(index: number) {
    const newPath = index === 0 ? '' : breadcrumbs.slice(0, index + 1).join('/');
    pathHistory = [];
    loadFiles(newPath);
    updateBreadcrumbs(newPath);
  }

  function openRename(item: FileItem) {
    selectedFile = item;
    openModal(RenameModal, {
      currentName: item.name,
      onRename: async (newName: string) => {
        const parentPath = item.path.substring(0, item.path.lastIndexOf('/'));
        const fullNewPath = parentPath ? `${parentPath}/${newName}` : newName;
        
        if (mode === 'admin') {
          await api.renameAdminFile(item.path, fullNewPath);
        } else {
          await api.renameFile(item.path, fullNewPath);
        }
        await loadFiles(currentPath);
      }
    });
  }

  function openDelete(item: FileItem) {
    selectedFile = item;
    openModal(ConfirmDialog, {
      title: 'Confirm Delete',
      message: `Are you sure you want to delete "${item.name}"?`,
      confirmText: 'Delete',
      danger: true,
      onConfirm: async () => {
        try {
          if (mode === 'admin') {
            await api.deleteAdminFile(item.path);
          } else {
            await api.deleteFile(item.path);
          }
          await loadFiles(currentPath);
        } catch (e: any) {
          error = e.message || 'Failed to delete';
        }
      }
    });
  }

  function downloadFile(item: FileItem) {
    if (mode === 'admin') {
      api.downloadAdminFile(item.path, item.name);
    }
  }

  function formatSize(bytes: number): string {
    if (bytes === 0) return '-';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  }
</script>

<div class="files-manager stagger-children">
  <div class="flex justify-between items-center mb-4">
    <h3 class="text-lg font-semibold">{title}</h3>
    <button class="glass-btn" onclick={() => loadFiles(currentPath)} disabled={loading}>
      {loading ? 'Loading...' : '🔄 Refresh'}
    </button>
  </div>

  {#if error}
    <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
      <p class="text-red-300 text-sm">{error}</p>
    </div>
  {/if}

  {#if mode === 'admin' || basePath || (files.length > 0 && files[0]?.path?.includes('/'))}
    <div class="glass-card mb-4">
      <div class="flex flex-wrap gap-3 items-center">
        <button class="glass-btn" onclick={navigateBack} disabled={pathHistory.length === 0}>
          ← Back
        </button>
        <div class="flex gap-2 items-center">
          <button class="text-blue-400 hover:text-blue-300" onclick={() => { pathHistory = []; loadFiles(''); updateBreadcrumbs(''); }}>
            {rootLabel}
          </button>
          {#each breadcrumbs as crumb, i}
            <span class="opacity-50">/</span>
            <button class="text-blue-400 hover:text-blue-300" onclick={() => goToBreadcrumb(i)}>
              {crumb}
            </button>
          {/each}
        </div>
        {#if mode === 'admin'}
          <span class="ml-auto text-sm opacity-75">
            {files.length} / {total} items
          </span>
        {/if}
      </div>
    </div>
  {/if}

  <div class="glass-card overflow-hidden">
    <table class="glass-table">
      <thead>
        <tr>
          <th>Name</th>
          <th>Size</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#if loading}
          <tr>
            <td colspan="3" class="text-center py-8 opacity-75">Loading...</td>
          </tr>
        {:else if files.length === 0}
          <tr>
            <td colspan="3" class="text-center py-8 opacity-75">No files found</td>
          </tr>
        {:else}
          {#each files as file}
            <tr>
              <td>
                <div class="flex items-center gap-2">
                  <span>{file.is_dir ? '📁' : '📄'}</span>
                  {#if file.is_dir}
                    <button class="text-blue-400 hover:text-blue-300" onclick={() => navigateToFolder(file.name)}>
                      {file.name}
                    </button>
                  {:else}
                    <span>{file.name}</span>
                  {/if}
                </div>
              </td>
              <td>{file.is_dir ? '-' : formatSize(file.size)}</td>
              <td>
                <div class="flex gap-2">
                  {#if mode === 'admin' && !file.is_dir}
                    <button class="glass-btn text-sm" onclick={() => downloadFile(file)}>
                      Download
                    </button>
                  {/if}
                  <button class="glass-btn text-sm" onclick={() => openRename(file)}>
                    Rename
                  </button>
                  <button class="glass-btn glass-btn-danger text-sm" onclick={() => openDelete(file)}>
                    Delete
                  </button>
                </div>
              </td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
    
    {#if hasMore && mode === 'admin'}
      <div class="p-4 text-center border-t border-white/10">
        <button 
          class="glass-btn" 
          onclick={loadMore} 
          disabled={loadingMore}
        >
          {loadingMore ? 'Loading more...' : `Load more (${total - files.length} remaining)`}
        </button>
      </div>
    {/if}
  </div>
</div>

<script lang="ts">
  import FilesManager from '../../components/FilesManager.svelte';
</script>

<div class="files-page stagger-children">
  <FilesManager 
    mode="user" 
    title="Downloads" 
    basePath="downloads"
    rootLabel="Downloads"
  />
</div>

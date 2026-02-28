<script lang="ts">
  import { onMount } from 'svelte';
  import { api } from '../../api/client';
  import { user } from '../../stores/auth';
  import { openModal } from '../../stores/modal';
  import { showToast } from '../../stores/toasts';
  import EditUserModal from '../../components/EditUserModal.svelte';
  import AddUserModal from '../../components/AddUserModal.svelte';
  import ConfirmDialog from '../../components/ConfirmDialog.svelte';

  let users: any[] = [];
  let loading = false;
  let filterText = '';
  let currentUserId: number | null = null;
  let currentUserIsAdmin = false;

  $: currentUserId = $user?.id ?? null;

  $: filteredUsers = users.filter(user => 
    user.username.toLowerCase().includes(filterText.toLowerCase()) ||
    user.email.toLowerCase().includes(filterText.toLowerCase())
  );

  onMount(async () => {
    await loadUsers();
    await loadEnvConfig();
  });

  async function loadEnvConfig() {
    try {
      const me = await api.getMe();
      currentUserIsAdmin = me.is_admin === true;
    } catch (e) {
      console.error('Failed to load user info:', e);
    }
  }

  async function loadUsers() {
    loading = true;
    try {
      users = await api.syncUsers();
    } catch (e: any) {
      showToast(e.message, 'error');
    } finally {
      loading = false;
    }
  }

  function isSuperAdmin(username: string): boolean {
    return username.toLowerCase() === 'admin';
  }

  function canEdit(userItem: any): boolean {
    if (isSuperAdmin(userItem.username)) return false;
    return true;
  }

  function canDelete(userItem: any): boolean {
    if (userItem.id === currentUserId) return false;
    if (isSuperAdmin(userItem.username)) return false;
    return true;
  }

  function openEdit(userItem: any) {
    openModal(EditUserModal, { 
      user: userItem, 
      isSuperAdmin: isSuperAdmin(userItem.username),
      onSave: loadUsers,
      onPasswordChange: () => {}
    });
  }

  function deleteUser(userId: number, username: string) {
    openModal(ConfirmDialog, {
      title: 'Delete User',
      message: `Are you sure you want to delete user "${username}"? This will delete all their data.`,
      confirmText: 'Delete',
      danger: true,
      onConfirm: async () => {
        try {
          await api.deleteUser(userId);
          await loadUsers();
          showToast('User deleted successfully', 'success');
        } catch (e: any) {
          showToast(e.message, 'error');
        }
      }
    });
  }
</script>

  <div class="users-page stagger-children">
    <div class="flex justify-between items-center mb-6 gap-3 min-w-0">
      <h2 class="text-xl font-bold whitespace-nowrap">User Management</h2>
      <div class="flex gap-2 items-center flex-shrink-0">
        <input type="text" bind:value={filterText} placeholder="Filter..." class="glass-input w-32" />
        <button class="glass-btn whitespace-nowrap" on:click={loadUsers} disabled={loading}>{loading ? 'Loading...' : '🔄 Refresh'}</button>
        {#if currentUserIsAdmin}
          <button class="glass-btn whitespace-nowrap" on:click={() => openModal(AddUserModal, { onUserCreated: loadUsers })}>➕ New User</button>
        {/if}
      </div>
    </div>

  <div class="glass-card overflow-hidden">
    <table class="glass-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>Username</th>
          <th>Email</th>
          <th>Admin</th>
          <th>Active</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {#each filteredUsers as user}
          <tr>
            <td>{user.id}</td>
            <td>
              {user.username}
              {#if isSuperAdmin(user.username)}
                <span class="ml-2 text-xs bg-yellow-500/20 text-yellow-400 px-2 py-0.5 rounded">Super Admin</span>
              {/if}
            </td>
            <td>{user.email}</td>
            <td>
              {#if user.is_admin}
                <span class="glass-badge glass-badge-info">Admin</span>
              {/if}
            </td>
            <td>
              {#if user.is_active}
                <span class="glass-badge glass-badge-success">Active</span>
              {:else}
                <span class="glass-badge glass-badge-error">Inactive</span>
              {/if}
            </td>
            <td>
              <div class="flex gap-2">
                <button 
                  class="glass-btn text-sm" 
                  on:click={() => openEdit(user)}
                  disabled={!canEdit(user)}
                  title={!canEdit(user) ? 'Cannot edit super admin' : ''}
                >
                  Edit
                </button>
                <button 
                  class="glass-btn glass-btn-danger text-sm" 
                  on:click={() => deleteUser(user.id, user.username)}
                  disabled={!canDelete(user)}
                  title={!canDelete(user) ? 'Cannot delete this user' : ''}
                >
                  Delete
                </button>
              </div>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>

    {#if filteredUsers.length === 0 && !loading}
      <div class="text-center py-12 opacity-75">
        {filterText ? 'No users match your filter' : 'No users found'}
      </div>
    {/if}
  </div>
</div>

<style>
</style>

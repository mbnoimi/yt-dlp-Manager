<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  import { closeModal } from '../stores/modal';
  import { api } from '../api/client';

  export let user: any;
  export let isSuperAdmin: boolean = false;
  export let onSave: () => void;
  export let onPasswordChange: () => void;

  let editUsername = user.username;
  let editEmail = user.email;
  let editIsAdmin = user.is_admin;
  let showPasswordForm = false;
  let newPassword = '';
  let saving = false;
  let error = '';
  let success = '';

  async function saveUser() {
    saving = true;
    error = '';
    success = '';

    try {
      const updateData: any = {
        username: editUsername,
        email: editEmail,
      };
      
      if (!isSuperAdmin) {
        updateData.is_admin = editIsAdmin;
      }
      
      await api.updateUser(user.id, updateData);
      success = 'User updated successfully';
      onSave();
      setTimeout(closeModal, 1000);
    } catch (e: any) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  async function changePassword() {
    if (!newPassword) return;
    saving = true;
    error = '';
    success = '';

    try {
      await api.changeUserPassword(user.id, newPassword);
      success = 'Password changed successfully';
      showPasswordForm = false;
      newPassword = '';
      onPasswordChange();
    } catch (e: any) {
      error = e.message;
    } finally {
      saving = false;
    }
  }

  function handleClose() {
    closeModal();
  }
</script>

<div class="glass-modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()}>
  <div class="glass-modal animate-scaleIn" on:click|stopPropagation>
    <h3 class="font-bold text-lg mb-4">Edit User: {user.username}</h3>
    
    <div class="mb-4">
      <label for="editUsername" class="block mb-2">Username</label>
      <input type="text" id="editUsername" bind:value={editUsername} class="glass-input" disabled={isSuperAdmin} />
    </div>

    <div class="mb-4">
      <label for="editEmail" class="block mb-2">Email</label>
      <input type="email" id="editEmail" bind:value={editEmail} class="glass-input" />
    </div>

    {#if !isSuperAdmin}
      <div class="mb-4">
        <label class="flex items-center gap-3 cursor-pointer">
          <input type="checkbox" bind:checked={editIsAdmin} class="w-5 h-5 rounded accent-blue-500" />
          <span class="font-medium">Admin User</span>
        </label>
      </div>
    {/if}

    {#if error}
      <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}

    {#if success}
      <div class="glass-card !p-3 !bg-green-500/20 border-green-500/30 mb-4">
        <p class="text-green-300 text-sm">{success}</p>
      </div>
    {/if}

    <div class="flex gap-3 flex-wrap">
      <button class="glass-btn glass-btn-primary" on:click={saveUser} disabled={saving}>
        {saving ? 'Saving...' : 'Save'}
      </button>
      <button class="glass-btn" on:click={() => showPasswordForm = !showPasswordForm}>
        {showPasswordForm ? 'Cancel' : 'Change Password'}
      </button>
      <button class="glass-btn" on:click={handleClose}>Close</button>
    </div>

    {#if showPasswordForm}
      <div class="mt-4 pt-4 border-t border-white/10">
        <h4 class="font-semibold mb-3">Change Password</h4>
        <div class="mb-3">
          <label for="newPassword" class="block mb-2">New Password</label>
          <input type="password" id="newPassword" bind:value={newPassword} placeholder="Enter new password" class="glass-input" />
        </div>
        <button class="glass-btn glass-btn-danger" on:click={changePassword} disabled={saving || !newPassword}>
          {saving ? 'Changing...' : 'Change Password'}
        </button>
      </div>
    {/if}
  </div>
</div>

<script lang="ts">
  import { user, loadUser, logout as authLogout } from '../stores/auth';
  import { api } from '../api/client';
  import { push } from 'svelte-spa-router';
  import { openModal } from '../stores/modal';
  import ConfirmDialog from '../components/ConfirmDialog.svelte';

  let showPasswordForm = false;
  let showUsernameForm = false;
  let showEmailForm = false;

  let currentPassword = '';
  let newPassword = '';
  let confirmPassword = '';
  let newUsername = '';
  let newEmail = '';
  
  let loading = false;
  let error = '';
  let success = '';

  let avatarInput: HTMLInputElement;
  let uploadingAvatar = false;

  async function handleAvatarSelect(event: Event) {
    const input = event.target as HTMLInputElement;
    if (!input.files || input.files.length === 0) return;
    
    const file = input.files[0];
    if (file.size > 2 * 1024 * 1024) {
      error = 'Avatar file must be less than 2MB';
      return;
    }

    uploadingAvatar = true;
    error = '';
    success = '';

    try {
      await api.uploadAvatar(file);
      await loadUser();
      success = 'Avatar updated successfully';
    } catch (e: any) {
      error = e.message;
    } finally {
      uploadingAvatar = false;
      input.value = '';
    }
  }

  async function changePassword() {
    if (newPassword !== confirmPassword) {
      error = 'Passwords do not match';
      return;
    }
    
    loading = true;
    error = '';
    success = '';
    
    try {
      await api.changePassword(currentPassword, newPassword);
      success = 'Password changed successfully';
      showPasswordForm = false;
      currentPassword = '';
      newPassword = '';
      confirmPassword = '';
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function changeUsername() {
    loading = true;
    error = '';
    success = '';
    
    try {
      await api.changeUsername(newUsername);
      success = 'Username changed successfully';
      showUsernameForm = false;
      newUsername = '';
      await loadUser();
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function changeEmail() {
    loading = true;
    error = '';
    success = '';
    
    try {
      await api.changeEmail(newEmail);
      success = 'Email changed successfully';
      showEmailForm = false;
      newEmail = '';
      await loadUser();
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  async function handleDeleteAccount() {
    loading = true;
    error = '';
    
    try {
      await api.deleteAccount();
      authLogout();
      push('/login');
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  function confirmDeleteAccount() {
    openModal(ConfirmDialog, {
      title: 'Delete Account',
      message: 'Are you sure you want to delete your account? This action cannot be undone.',
      confirmText: 'Delete',
      danger: true,
      onConfirm: handleDeleteAccount
    });
  }
</script>

<div class="max-w-2xl mx-auto stagger-children">
  {#if error}
    <div class="glass-card !bg-red-500/20 border-red-500/30">
      <p class="text-red-300">{error}</p>
    </div>
  {/if}

  {#if success}
    <div class="glass-card !bg-green-500/20 border-green-500/30">
      <p class="text-green-300">{success}</p>
    </div>
  {/if}

  <div class="glass-card">
    <h2 class="text-xl font-bold mb-6">Profile Settings</h2>
    
    <div class="flex items-start gap-6 mb-6">
      <div class="relative">
        <button 
          class="w-24 h-24 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center text-3xl font-bold text-white border-4 border-white/20 shadow-lg"
          on:click={() => avatarInput.click()}
          disabled={uploadingAvatar}
        >
          {#if $user?.avatar}
            <img src={$user.avatar} alt="Avatar" class="w-full h-full object-cover rounded-full" />
          {:else}
            {$user?.username?.charAt(0).toUpperCase() || 'U'}
          {/if}
        </button>
        <div class="absolute bottom-0 right-0 w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center shadow-lg cursor-pointer" on:click={() => avatarInput.click()}>
          <span class="text-sm">✏️</span>
        </div>
        <input
          type="file"
          accept="image/*"
          bind:this={avatarInput}
          on:change={handleAvatarSelect}
          style="display: none"
        />
      </div>
      
      <div class="flex-1">
        <h3 class="text-lg font-semibold">{$user?.username}</h3>
        <p class="opacity-75">{$user?.email}</p>
        <div class="mt-2">
          {#if $user?.is_admin}
            <span class="glass-badge glass-badge-info">Administrator</span>
          {:else}
            <span class="glass-badge glass-badge-success">User</span>
          {/if}
        </div>
      </div>
    </div>

    <div class="flex gap-4 flex-wrap">
      <button class="glass-btn" on:click={() => showPasswordForm = !showPasswordForm}>
        Change Password
      </button>
      
      <button class="glass-btn" on:click={() => showUsernameForm = !showUsernameForm}>
        Change Username
      </button>

      <button class="glass-btn" on:click={() => showEmailForm = !showEmailForm}>
        Change Email
      </button>
    </div>

    {#if showEmailForm}
      <div class="mt-6 p-4 bg-white/5 rounded-xl">
        <h3 class="font-semibold mb-4">Change Email</h3>
        <form on:submit|preventDefault={changeEmail} class="flex flex-col gap-4">
          <div>
            <label for="newEmail">New Email</label>
            <input type="email" id="newEmail" bind:value={newEmail} class="glass-input" required />
          </div>
          <div class="flex gap-3">
            <button type="submit" class="glass-btn glass-btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save'}
            </button>
            <button type="button" class="glass-btn" on:click={() => showEmailForm = false}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    {/if}

    {#if showPasswordForm}
      <div class="mt-6 p-4 bg-white/5 rounded-xl">
        <h3 class="font-semibold mb-4">Change Password</h3>
        <form on:submit|preventDefault={changePassword} class="flex flex-col gap-4">
          <div>
            <label for="currentPassword">Current Password</label>
            <input type="password" id="currentPassword" bind:value={currentPassword} class="glass-input" required />
          </div>
          <div>
            <label for="newPassword">New Password</label>
            <input type="password" id="newPassword" bind:value={newPassword} class="glass-input" required />
          </div>
          <div>
            <label for="confirmPassword">Confirm New Password</label>
            <input type="password" id="confirmPassword" bind:value={confirmPassword} class="glass-input" required />
          </div>
          <div class="flex gap-3">
            <button type="submit" class="glass-btn glass-btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save'}
            </button>
            <button type="button" class="glass-btn" on:click={() => showPasswordForm = false}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    {/if}

    {#if showUsernameForm}
      <div class="mt-6 p-4 bg-white/5 rounded-xl">
        <h3 class="font-semibold mb-4">Change Username</h3>
        <form on:submit|preventDefault={changeUsername} class="flex flex-col gap-4">
          <div>
            <label for="newUsername">New Username</label>
            <input type="text" id="newUsername" bind:value={newUsername} class="glass-input" required />
          </div>
          <div class="flex gap-3">
            <button type="submit" class="glass-btn glass-btn-primary" disabled={loading}>
              {loading ? 'Saving...' : 'Save'}
            </button>
            <button type="button" class="glass-btn" on:click={() => showUsernameForm = false}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    {/if}

    {#if !$user?.is_admin}
      <div class="mt-6 p-4 bg-white/5 rounded-xl border border-red-500/30">
        <h3 class="font-semibold mb-2 text-red-400">Danger Zone</h3>
        <p class="text-sm opacity-75 mb-4">Once you delete your account, there is no going back.</p>
        <button 
          class="glass-btn !bg-red-500/20 !border-red-500/30 !text-red-400 hover:!bg-red-500/30" 
          on:click={confirmDeleteAccount}
          disabled={loading}
        >
          Delete Account
        </button>
      </div>
    {/if}
  </div>
</div>

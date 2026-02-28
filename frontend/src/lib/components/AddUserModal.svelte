<script lang="ts">
  import { closeModal } from '../stores/modal';
  import { api } from '../api/client';
  import { showToast } from '../stores/toasts';

  export let onUserCreated: () => void;

  let username = '';
  let email = '';
  let password = '';
  let saving = false;
  let error = '';

  async function createUser() {
    if (!username || !email || !password) {
      error = 'Please fill in all fields';
      return;
    }

    saving = true;
    error = '';

    try {
      await api.createUser(username, email, password);
      showToast('User created successfully', 'success');
      closeModal();
      if (onUserCreated) onUserCreated();
    } catch (e: any) {
      error = e.message || 'Failed to create user';
    } finally {
      saving = false;
    }
  }

  function handleClose() {
    closeModal();
  }
</script>

<div class="glass-modal-overlay" on:click={handleClose} on:keydown={(e) => e.key === 'Escape' && handleClose()}>
  <div class="glass-modal animate-scaleIn" on:click|stopPropagation on:keydown|stopPropagation>
    <h3 class="text-lg font-bold mb-4">Create New User</h3>
    
    {#if error}
      <div class="glass-card !p-3 !bg-red-500/20 border-red-500/30 mb-4">
        <p class="text-red-300 text-sm">{error}</p>
      </div>
    {/if}
    
    <div class="space-y-4">
      <div>
        <label class="block text-sm mb-1">Username</label>
        <input 
          type="text" 
          bind:value={username} 
          class="glass-input w-full"
          placeholder="username"
        />
      </div>
      
      <div>
        <label class="block text-sm mb-1">Email</label>
        <input 
          type="email" 
          bind:value={email} 
          class="glass-input w-full"
          placeholder="email@example.com"
        />
      </div>
      
      <div>
        <label class="block text-sm mb-1">Password</label>
        <input 
          type="password" 
          bind:value={password} 
          class="glass-input w-full"
          placeholder="••••••••"
        />
      </div>
    </div>
    
    <div class="flex justify-end gap-3 mt-6">
      <button class="glass-btn" on:click={handleClose}>
        Cancel
      </button>
      <button class="glass-btn" on:click={createUser} disabled={saving}>
        {saving ? 'Creating...' : 'Create User'}
      </button>
    </div>
  </div>
</div>

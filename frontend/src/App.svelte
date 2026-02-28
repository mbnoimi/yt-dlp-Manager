<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import Router, { push, location } from 'svelte-spa-router';
  import { user, loadUser, isAuthenticated, isAdmin, logout as authLogout } from './lib/stores/auth';
  import { startSSE, stopSSE } from './lib/stores/downloads';
  import ConfirmDialog from './lib/components/ConfirmDialog.svelte';
  import Toast from './lib/components/Toast.svelte';
  import Dropdown from './lib/components/Dropdown.svelte';
  import { modalOutlet, openModal, type ModalProps } from './lib/stores/modal';

  let currentModal: ModalProps | null = null;

  $: currentModal = $modalOutlet;

  $: modalComponent = currentModal?.component;
  $: modalProps = currentModal?.props ?? {};

  import Login from './lib/pages/Login.svelte';
  import Register from './lib/pages/Register.svelte';
  import Dashboard from './lib/pages/Dashboard.svelte';
  import Profile from './lib/pages/Profile.svelte';
  import About from './lib/pages/About.svelte';
  import ServerManager from './lib/pages/ServerManager.svelte';

  const routes = {
    '/': Dashboard,
    '/login': Login,
    '/register': Register,
    '/dashboard': Dashboard,
    '/profile': Profile,
    '/about': About,
    '/server-manager': ServerManager,
  };

  let currentPath = '';
  let menuOpen = false;
  
  location.subscribe(value => {
    currentPath = value;
  });

  $: if ($isAuthenticated && (currentPath === '/' || currentPath === '/login' || currentPath === '/register')) {
    push('/dashboard');
  }

  $: if (!$isAuthenticated && currentPath !== '/register') {
    push('/login');
  }

  onMount(async () => {
    await loadUser();
    if ($isAuthenticated) {
      startSSE();
    }
  });

  function handleLogout() {
    stopSSE();
    authLogout();
    push('/login');
    menuOpen = false;
  }

  function confirmLogout() {
    openModal(ConfirmDialog, {
      title: 'Logout',
      message: 'Are you sure you want to logout?',
      confirmText: 'Logout',
      danger: true,
      onConfirm: handleLogout
    });
  }

  function closeMenu() {
    menuOpen = false;
  }
</script>

<div id="app">
  {#if $isAuthenticated}
    <nav class="glass-nav">
      <div class="nav-brand">
        <a href="#/dashboard" class="brand-link">
          <span class="brand-icon">▶</span>
          <span class="brand-text">yt-dlp Manager</span>
        </a>
      </div>
      <div class="nav-links">
        <div class="dropdown relative">
          <button class="glass-avatar" on:click={() => menuOpen = !menuOpen}>
            {#if $user?.avatar}
              <img src={$user.avatar} alt="Avatar" />
            {:else}
              {$user?.username?.charAt(0).toUpperCase() || 'U'}
            {/if}
          </button>
          {#if menuOpen}
            <div class="glass-dropdown absolute right-0 top-full mt-2 animate-scaleIn" style="white-space: nowrap;">
              
              <a href="#/profile" class="glass-dropdown-item block" style="white-space: nowrap;" on:click={closeMenu}>
                {$user?.username || 'User'}
              </a>
              {#if $user?.is_admin}
                <a href="#/server-manager" class="glass-dropdown-item block" style="white-space: nowrap;" on:click={closeMenu}>
                  Server Manager
                </a>
              {/if}
              <a href="#/about" class="glass-dropdown-item block" style="white-space: nowrap;" on:click={closeMenu}>
                About
              </a>
              <div class="border-t border-white/10 mt-2 pt-2">
                <button class="glass-dropdown-item block w-full text-left text-red-400" style="white-space: nowrap;" on:click={() => { menuOpen = false; confirmLogout(); }}>
                  Logout
                </button>
              </div>
            </div>
          {/if}
        </div>
      </div>
    </nav>
  {/if}

  <main class:has-nav={$isAuthenticated} style="overflow: visible;">
    <div style="overflow: visible;">
      <Router {routes} />
    </div>
  </main>
</div>

<Toast />

<Dropdown />

{#if modalComponent}
  <svelte:component this={modalComponent} {...modalProps} />
{/if}

<style>
  #app {
    min-height: 100vh;
    position: relative;
    overflow: visible;
  }

  #app > * {
    overflow: visible;
  }

  .nav-brand {
    display: flex;
    align-items: center;
  }

  .brand-link {
    display: flex;
    align-items: center;
    gap: 10px;
    text-decoration: none;
    color: var(--glass-text);
  }

  .brand-icon {
    width: 36px;
    height: 36px;
    background: linear-gradient(135deg, #007AFF 0%, #5856D6 100%);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 14px;
  }

  .brand-text {
    font-size: 20px;
    font-weight: 700;
    letter-spacing: -0.5px;
  }

  .nav-links {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  main {
    flex: 1;
    padding: 24px;
    max-width: 1400px;
    margin: 0 auto;
    width: 100%;
    overflow: visible;
  }

  main.has-nav {
    padding-top: 32px;
  }
</style>

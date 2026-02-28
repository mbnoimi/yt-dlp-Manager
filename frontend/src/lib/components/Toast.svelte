<script lang="ts">
  import { toasts, removeToast, pauseToast, resumeToast } from '../stores/toasts';
</script>

{#if $toasts.length > 0}
  <div class="toast-overlay">
    {#each $toasts as toast (toast.id)}
      <div 
        class="toast-item animate-scaleIn"
        class:toast-success={toast.type === 'success'}
        class:toast-error={toast.type === 'error'}
        class:toast-info={toast.type === 'info'}
        on:mouseenter={() => pauseToast(toast.id)}
        on:mouseleave={() => resumeToast(toast.id)}
        on:touchstart={() => pauseToast(toast.id)}
        on:touchend={() => resumeToast(toast.id)}
      >
        <div class="toast-header">
          <span class="toast-title">
            {#if toast.type === 'success'}
              Success
            {:else if toast.type === 'error'}
              Error
            {:else}
              Info
            {/if}
          </span>
          <button class="toast-close" on:click={() => removeToast(toast.id)}>✕</button>
        </div>
        <div class="toast-content">
          {toast.message}
        </div>
      </div>
    {/each}
  </div>
{/if}

<style>
  .toast-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(0, 0, 0, 0.5);
    gap: 12px;
  }

  .toast-item {
    background: linear-gradient(180deg, rgba(30, 30, 50, 0.98) 0%, rgba(20, 20, 35, 0.98) 100%);
    backdrop-filter: blur(16px);
    border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.12));
    border-radius: 14px;
    padding: 16px 20px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    max-width: 400px;
    width: 90%;
    max-height: 60vh;
    display: flex;
    flex-direction: column;
  }

  .toast-success {
    border-color: rgba(16, 185, 129, 0.4);
    background: linear-gradient(180deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.08) 100%);
  }

  .toast-error {
    border-color: rgba(239, 68, 68, 0.4);
    background: linear-gradient(180deg, rgba(239, 68, 68, 0.15) 0%, rgba(239, 68, 68, 0.08) 100%);
  }

  .toast-info {
    border-color: rgba(59, 130, 246, 0.4);
    background: linear-gradient(180deg, rgba(59, 130, 246, 0.15) 0%, rgba(59, 130, 246, 0.08) 100%);
  }

  .toast-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .toast-title {
    font-weight: 600;
    font-size: 16px;
    color: rgba(255, 255, 255, 0.95);
  }

  .toast-success .toast-title {
    color: #34D399;
  }

  .toast-error .toast-title {
    color: #F87171;
  }

  .toast-info .toast-title {
    color: #60A5FA;
  }

  .toast-content {
    color: rgba(255, 255, 255, 0.85);
    font-size: 14px;
    line-height: 1.5;
    overflow-y: auto;
    max-height: 200px;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .toast-close {
    background: none;
    border: none;
    color: rgba(255, 255, 255, 0.5);
    font-size: 16px;
    cursor: pointer;
    padding: 4px 8px;
    line-height: 1;
    transition: color 0.2s;
  }

  .toast-close:hover {
    color: rgba(255, 255, 255, 0.9);
  }

  @keyframes scaleIn {
    from {
      opacity: 0;
      transform: scale(0.9);
    }
    to {
      opacity: 1;
      transform: scale(1);
    }
  }

  .animate-scaleIn {
    animation: scaleIn 0.2s ease-out;
  }
</style>

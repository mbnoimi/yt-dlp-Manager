import { writable } from 'svelte/store';

export const toasts = writable<Array<{
  id: number;
  message: string;
  type: 'success' | 'error' | 'info';
  timeout: ReturnType<typeof setTimeout> | null;
}>>([]);

let toastId = 0;

export function showToast(message: string, type: 'success' | 'error' | 'info' = 'info', duration = 4000) {
  const id = ++toastId;
  
  const timeout = setTimeout(() => {
    toasts.update(t => t.filter(toast => toast.id !== id));
  }, duration);
  
  toasts.update(t => [...t, { id, message, type, timeout }]);
}

export function removeToast(id: number) {
  toasts.update(t => {
    const toast = t.find(item => item.id === id);
    if (toast?.timeout) {
      clearTimeout(toast.timeout);
    }
    return t.filter(item => item.id !== id);
  });
}

export function pauseToast(id: number) {
  toasts.update(t => t.map(toast => {
    if (toast.id === id && toast.timeout) {
      clearTimeout(toast.timeout);
      toast.timeout = null;
    }
    return toast;
  }));
}

export function resumeToast(id: number, duration = 4000) {
  toasts.update(t => t.map(toast => {
    if (toast.id === id && !toast.timeout) {
      toast.timeout = setTimeout(() => {
        toasts.update(items => items.filter(item => item.id !== id));
      }, duration);
    }
    return toast;
  }));
}

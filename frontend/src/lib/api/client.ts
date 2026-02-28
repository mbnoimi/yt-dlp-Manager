const API_URL = '';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('token', token);
    } else {
      localStorage.removeItem('token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers as Record<string, string>,
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'An error occurred' }));
      
      let errorMessage = errorData.detail;
      
      if (Array.isArray(errorData.detail)) {
        errorMessage = errorData.detail.map((e: any) => {
          const field = e.loc ? e.loc.slice(1).join('.') : 'field';
          return `${field}: ${e.msg}`;
        }).join(', ');
      }
      
      throw new Error(errorMessage || 'An error occurred');
    }

    if (response.status === 204) {
      return undefined as T;
    }

    return response.json();
  }

  // Auth
  async login(username: string, password: string): Promise<{ access_token: string; token_type: string }> {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Login failed' }));
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    this.setToken(data.access_token);
    return data;
  }

  async register(username: string, email: string, password: string): Promise<any> {
    return this.request('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async getMe(): Promise<any> {
    return this.request('/api/v1/auth/me');
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    return this.request('/api/v1/auth/me/password', {
      method: 'POST',
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  async changeUsername(newUsername: string): Promise<void> {
    return this.request('/api/v1/auth/me/username', {
      method: 'PUT',
      body: JSON.stringify({ new_username: newUsername }),
    });
  }

  async changeEmail(newEmail: string): Promise<any> {
    return this.request('/api/v1/auth/me/email', {
      method: 'PUT',
      body: JSON.stringify({ new_email: newEmail }),
    });
  }

  async updateAvatar(avatar: string): Promise<any> {
    return this.request('/api/v1/auth/me/avatar', {
      method: 'PUT',
      body: JSON.stringify({ avatar }),
    });
  }

  async uploadAvatar(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/v1/auth/me/avatar`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async deleteAccount(): Promise<void> {
    return this.request('/api/v1/auth/me', { method: 'DELETE' });
  }

  // Users (admin)
  async getUsers(): Promise<any[]> {
    return this.request('/api/v1/auth/users');
  }

  async syncUsers(): Promise<any[]> {
    return this.request('/api/v1/auth/users/sync', { method: 'POST' });
  }

  async createUser(username: string, email: string, password: string): Promise<any> {
    return this.request('/api/v1/auth/users', {
      method: 'POST',
      body: JSON.stringify({ username, email, password }),
    });
  }

  async updateUser(userId: number, data: { username?: string; email?: string; is_admin?: boolean }): Promise<any> {
    return this.request(`/api/v1/auth/users/${userId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  }

  async changeUserPassword(userId: number, newPassword: string): Promise<void> {
    return this.request(`/api/v1/auth/users/${userId}/password`, {
      method: 'POST',
      body: JSON.stringify({ new_password: newPassword }),
    });
  }

  async deleteUser(userId: number): Promise<void> {
    return this.request(`/api/v1/auth/users/${userId}`, { method: 'DELETE' });
  }

  logout() {
    this.setToken(null);
  }

  // Configs
  async getConfigs(): Promise<{ name: string }[]> {
    return this.request('/api/v1/configs/');
  }

  async getConfig(name: string): Promise<{ content: string }> {
    return this.request(`/api/v1/configs/${name}`);
  }

  async saveConfig(name: string, content: string): Promise<void> {
    return this.request(`/api/v1/configs/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteConfig(name: string): Promise<void> {
    return this.request(`/api/v1/configs/${name}`, { method: 'DELETE' });
  }

  async uploadCookies(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/v1/configs/cookies`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
      throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
  }

  async resetArchive(): Promise<{ message: string }> {
    return this.request('/api/v1/configs/reset-archive', { method: 'POST' });
  }

  // URLs
  async getUrls(): Promise<{ name: string }[]> {
    return this.request('/api/v1/urls/');
  }

  async getUrlSource(name: string): Promise<{ content: string }> {
    return this.request(`/api/v1/urls/${name}`);
  }

  async saveUrlSource(name: string, content: string): Promise<void> {
    return this.request(`/api/v1/urls/${name}`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  }

  async deleteUrlSource(name: string): Promise<void> {
    return this.request(`/api/v1/urls/${name}`, { method: 'DELETE' });
  }

  // Downloads
  async getDownloadSources(): Promise<{ name: string }[]> {
    return this.request('/api/v1/downloads/');
  }

  async startDownload(name: string, createSymlinks: boolean = true): Promise<any> {
    return this.request(`/api/v1/downloads/${name}`, {
      method: 'POST',
      body: JSON.stringify({ create_symlinks: createSymlinks }),
    });
  }

  async getJobStatus(jobId: number): Promise<any> {
    return this.request(`/api/v1/downloads/status/${jobId}`);
  }

  async stopJob(jobId: number): Promise<void> {
    return this.request(`/api/v1/downloads/stop/${jobId}`, { method: 'POST', body: JSON.stringify({}) });
  }

  async cancelJob(jobId: number): Promise<void> {
    return this.request(`/api/v1/downloads/cancel/${jobId}`, { method: 'POST', body: JSON.stringify({}) });
  }

  async cancelAllJobs(): Promise<void> {
    return this.request('/api/v1/downloads/cancel-all', { method: 'POST', body: JSON.stringify({}) });
  }

  async stopAllJobs(): Promise<void> {
    return this.request('/api/v1/downloads/stop-all', { method: 'POST', body: JSON.stringify({}) });
  }

  // Files
  async getFiles(path: string = ''): Promise<{ path: string; is_dir: boolean; size: number }[]> {
    let query = '';
    if (path) {
      query = `?path=${encodeURIComponent(path)}`;
    }
    return this.request(`/api/v1/files/${query}`);
  }

  async deleteFile(path: string): Promise<void> {
    return this.request(`/api/v1/files/${encodeURIComponent(path)}`, { method: 'DELETE' });
  }

  async renameFile(oldPath: string, newPath: string): Promise<void> {
    return this.request(`/api/v1/files/rename?old_path=${encodeURIComponent(oldPath)}&new_path=${encodeURIComponent(newPath)}`, {
      method: 'POST'
    });
  }

  // Admin Files
  async getAdminFiles(path: string = '', offset: number = 0, limit: number = 50): Promise<{ files: { path: string; is_dir: boolean; size: number; modified: string }[]; total: number; has_more: boolean }> {
    let query = `?offset=${offset}&limit=${limit}`;
    if (path) {
      query += `&path=${encodeURIComponent(path)}`;
    }
    return this.request(`/api/v1/admin/files/${query}`);
  }

  async deleteAdminFile(path: string): Promise<void> {
    return this.request(`/api/v1/admin/files/${path}`, { method: 'DELETE' });
  }

  async renameAdminFile(oldPath: string, newPath: string): Promise<void> {
    return this.request(`/api/v1/admin/files/rename?old_path=${encodeURIComponent(oldPath)}&new_path=${encodeURIComponent(newPath)}`, {
      method: 'POST'
    });
  }

  async downloadAdminFile(path: string, filename: string): Promise<void> {
    const token = this.getToken();
    const response = await fetch(`/api/v1/admin/files/download/${encodeURIComponent(path)}`, {
      headers: token ? { 'Authorization': `Bearer ${token}` } : {}
    });
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Download failed');
    }
    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  }

  // Logs
  async getUserLogs(): Promise<string> {
    return this.request('/api/v1/logs/user');
  }

  async getBackendLogs(): Promise<string> {
    return this.request('/api/v1/logs/backend');
  }

  async getServerLogs(): Promise<string> {
    return this.request('/api/v1/logs/server');
  }

  async getUserLogsByUsername(username: string): Promise<string> {
    return this.request(`/api/v1/logs/by-user/${username}`);
  }

  // System
  async getSystemCheck(): Promise<{
    yt_dlp_installed: boolean;
    yt_dlp_version: string;
    deno_installed: boolean;
    deno_version: string;
  }> {
    return this.request('/api/v1/system/check');
  }

  async getVersion(): Promise<{ version: string }> {
    return this.request('/api/v1/system/version');
  }

  async getAppInfo(): Promise<{ title: string; description: string; version: string }> {
    return this.request('/api/v1/system/app-info');
  }

  async upgradeYtDlp(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/v1/system/upgrade', { method: 'POST' });
  }

  async getServerInfo(): Promise<any> {
    return this.request('/api/v1/system/server-info');
  }

  async getEnvConfig(): Promise<any> {
    return this.request('/api/v1/system/env-config');
  }

  async healthCheck(): Promise<any> {
    try {
      const response = await fetch(`${API_URL}/health`);
      if (!response.ok) {
        throw new Error('Server not available');
      }
      return response.json();
    } catch (e) {
      throw new Error('Server not available');
    }
  }

  async updateEnvConfig(config: Record<string, string | number | boolean>): Promise<any> {
    return this.request('/api/v1/system/env-config', {
      method: 'PUT',
      body: JSON.stringify(config),
    });
  }

  async restartServer(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/v1/system/restart', { method: 'POST' });
  }

  async shutdownServer(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/v1/system/shutdown', { method: 'POST' });
  }

  async getRunningJobs(): Promise<any[]> {
    return this.request('/api/v1/downloads/running');
  }

  async getUsersWithJobs(): Promise<any[]> {
    return this.request('/api/v1/downloads/users-with-jobs');
  }

  // SSE for running jobs
  createSSE(): EventSource {
    const token = this.getToken();
    const url = token 
      ? `${API_URL}/api/v1/downloads/running?token=${encodeURIComponent(token)}`
      : `${API_URL}/api/v1/downloads/running`;
    return new EventSource(url);
  }

  // Scheduler
  async getScheduledTasks(): Promise<any[]> {
    return this.request('/api/v1/tasks/');
  }

  async getScheduledTask(taskId: number): Promise<any> {
    return this.request(`/api/v1/tasks/${taskId}`);
  }

  async createScheduledTask(task: {
    name: string;
    task_type: string;
    datasource?: string;
    cron_expression: string;
    config?: string;
    target_user_id?: number;
  }): Promise<any> {
    return this.request('/api/v1/tasks/', {
      method: 'POST',
      body: JSON.stringify(task),
    });
  }

  async updateScheduledTask(taskId: number, task: {
    name?: string;
    task_type?: string;
    datasource?: string;
    cron_expression?: string;
    config?: string;
    is_active?: boolean;
  }): Promise<any> {
    return this.request(`/api/v1/tasks/${taskId}`, {
      method: 'PUT',
      body: JSON.stringify(task),
    });
  }

  async deleteScheduledTask(taskId: number): Promise<void> {
    return this.request(`/api/v1/tasks/${taskId}`, {
      method: 'DELETE',
    });
  }

  async getAllScheduledTasks(): Promise<any[]> {
    return this.request('/api/v1/tasks/admin/tasks');
  }

  async cleanupOldFiles(days: number): Promise<{ files_deleted: number; folders_deleted: number; space_freed: number }> {
    return this.request('/api/v1/tasks/cleanup', {
      method: 'POST',
      body: JSON.stringify({ days }),
    });
  }

  async countOldFiles(days: number): Promise<{ files_count: number; folders_count: number; total_size: number }> {
    return this.request(`/api/v1/tasks/cleanup/count?days=${days}`);
  }
}

export const api = new ApiClient();

document.addEventListener('alpine:init', () => {
  Alpine.store('wmStudio', {
    mode: 'projects',
    recentSnapshots: [],
    snapshotFilters: { scope: '', desktop_number: '', project_id: '' },
    snapshotDetail: null,
    snapshotEdit: { title: '', note: '', is_pinned: false },
    restorePlan: null,
    projects: [],
    activeProject: null,
    newProject: { manual_name: '', root_path: '', notes: '' },
    launchResult: null,

    init() {
      this.loadProjects();
      this.loadRecentSnapshots();
    },

    async saveSnapshot() {
      await fetch('/api/snapshots', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title: 'Quick Snapshot' })
      });
      await this.loadRecentSnapshots();
    },

    async loadRecentSnapshots() {
      const params = new URLSearchParams();
      params.set('limit', '20');
      if (this.snapshotFilters.scope) params.set('scope', this.snapshotFilters.scope);
      if (this.snapshotFilters.desktop_number) params.set('desktop_number', this.snapshotFilters.desktop_number);
      if (this.snapshotFilters.project_id) params.set('project_id', this.snapshotFilters.project_id);
      const response = await fetch(`/api/snapshots?${params.toString()}`);
      const data = await response.json();
      this.recentSnapshots = data.items || [];
    },

    async openSnapshot(snapshotId) {
      const detailRes = await fetch(`/api/snapshots/${snapshotId}`);
      this.snapshotDetail = await detailRes.json();
      this.snapshotEdit.title = this.snapshotDetail.snapshot.title || '';
      this.snapshotEdit.note = this.snapshotDetail.snapshot.note || '';
      this.snapshotEdit.is_pinned = !!this.snapshotDetail.snapshot.is_pinned;
      await this.loadRestorePlan();
    },

    async saveSnapshotMeta() {
      if (!this.snapshotDetail) return;
      await fetch(`/api/snapshots/${this.snapshotDetail.snapshot.id}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.snapshotEdit)
      });
      await this.openSnapshot(this.snapshotDetail.snapshot.id);
      await this.loadRecentSnapshots();
    },

    async loadRestorePlan() {
      if (!this.snapshotDetail) return;
      const response = await fetch(`/api/snapshots/${this.snapshotDetail.snapshot.id}/restore-plan`, { method: 'POST' });
      this.restorePlan = await response.json();
    },

    async restoreSnapshot(snapshotId) {
      await fetch(`/api/snapshots/${snapshotId}/restore`, { method: 'POST' });
      await this.openSnapshot(snapshotId);
    },

    async loadProjects() {
      const response = await fetch('/api/projects');
      const data = await response.json();
      this.projects = data.items || [];
    },

    async createProject() {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(this.newProject)
      });
      if (!response.ok) throw new Error('Failed to create project');
      this.newProject = { manual_name: '', root_path: '', notes: '' };
      await this.loadProjects();
    },

    async selectProject(projectId) {
      const response = await fetch(`/api/projects/${projectId}`);
      this.activeProject = await response.json();
    },

    async deleteProject(projectId) {
      await fetch(`/api/projects/${projectId}`, { method: 'DELETE' });
      if (this.activeProject?.id === projectId) this.activeProject = null;
      await this.loadProjects();
    },

    async addDefaultTerminal() {
      if (!this.activeProject) return;
      await fetch(`/api/projects/${this.activeProject.id}/terminals`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: 'Terminal', cwd: this.activeProject.root_path, preferred_zone: 'left' })
      });
      await this.selectProject(this.activeProject.id);
    },

    async addDefaultApp() {
      if (!this.activeProject) return;
      await fetch(`/api/projects/${this.activeProject.id}/apps`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ app_type: 'vscode', display_name: 'VS Code', launch_target: this.activeProject.root_path, preferred_zone: 'right' })
      });
      await this.selectProject(this.activeProject.id);
    },

    async launchProject(projectId) {
      const response = await fetch(`/api/projects/${projectId}/launch`, { method: 'POST' });
      this.launchResult = await response.json();
    }
  });
});

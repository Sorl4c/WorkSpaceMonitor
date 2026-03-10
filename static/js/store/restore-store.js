document.addEventListener('alpine:init', () => {
  Alpine.store('wmRestore', {
    snapshot: null,
    restorePlan: null,
    restoreResult: null,
    desktops: [],
    loading: false,
    loadingPlan: false,
    restoring: false,
    target: { mode: 'same', desktop_number: null },

    async init() {
      this.loading = true;
      try {
        await this.loadDesktops();
        await this.loadSnapshot();
        await this.refreshPlan();
      } finally {
        this.loading = false;
      }
    },

    async loadDesktops() {
      const response = await fetch('/desktops');
      this.desktops = await response.json();
      if (!this.target.desktop_number && this.desktops.length > 0) {
        this.target.desktop_number = this.desktops[0].number;
      }
    },

    async loadSnapshot() {
      const response = await fetch('/api/json-snapshot');
      if (!response.ok) {
        this.snapshot = null;
        this.restorePlan = null;
        return;
      }
      this.snapshot = await response.json();
      if (this.target.mode === 'same' && this.snapshot?.desktop?.number) {
        this.target.desktop_number = this.snapshot.desktop.number;
      }
    },

    targetPayload() {
      return {
        target: {
          mode: this.target.mode,
          desktop_number: this.target.mode === 'desktop' ? this.target.desktop_number : null,
        }
      };
    },

    async refreshPlan() {
      if (!this.snapshot) return;
      this.loadingPlan = true;
      try {
        const response = await fetch('/api/json-snapshot/restore-plan', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.targetPayload())
        });
        if (!response.ok) throw new Error('Failed to load restore plan');
        this.restorePlan = await response.json();
      } finally {
        this.loadingPlan = false;
      }
    },

    async restore() {
      if (!this.snapshot) return;
      this.restoring = true;
      try {
        const response = await fetch('/api/json-snapshot/restore', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(this.targetPayload())
        });
        if (!response.ok) throw new Error('Failed to restore snapshot');
        this.restoreResult = await response.json();
        await this.loadDesktops();
        await this.refreshPlan();
      } finally {
        this.restoring = false;
      }
    }
  });
});

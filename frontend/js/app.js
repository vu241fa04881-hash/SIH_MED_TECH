/**
 * MoveAssist Orchestrator & SSE Streaming Client
 * SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
 */

document.addEventListener('DOMContentLoaded', () => {
  // Initialize Subsystems
  const viewer = new MoveAssist3DViewer('three-canvas-container');
  const schematic2D = new MoveAssist2DSchematic('schematic-2d-canvas');
  const charts = new MoveAssistChartsManager();
  const dashboard = new MoveAssistDashboard(viewer, charts);

  // Split View Mode Management
  const viewportStage = document.getElementById('viewport-stage');
  const btnViewSplit = document.getElementById('btn-view-split');
  const btnView3D = document.getElementById('btn-view-3d');
  const btnView2D = document.getElementById('btn-view-2d');
  const titleModeText = document.getElementById('viewport-mode-title');
  const titleModeIcon = document.getElementById('viewport-mode-icon');

  function setViewMode(mode) {
    btnViewSplit?.classList.remove('active');
    btnView3D?.classList.remove('active');
    btnView2D?.classList.remove('active');

    viewportStage.className = 'viewport-stage';

    if (mode === 'split') {
      viewportStage.classList.add('split-view');
      btnViewSplit?.classList.add('active');
      if (titleModeText) titleModeText.textContent = 'Digital Twin (3D + 2D Split View)';
      if (titleModeIcon) titleModeIcon.textContent = '◫';
    } else if (mode === '3d') {
      viewportStage.classList.add('view-3d-only');
      btnView3D?.classList.add('active');
      if (titleModeText) titleModeText.textContent = '3D Virtual Human & Exoskeleton Digital Twin';
      if (titleModeIcon) titleModeIcon.textContent = '🦾';
    } else if (mode === '2d') {
      viewportStage.classList.add('view-2d-only');
      btnView2D?.classList.add('active');
      if (titleModeText) titleModeText.textContent = '2D Biomechanical & Actuator Engineering Schematic';
      if (titleModeIcon) titleModeIcon.textContent = '📐';
    }

    // Trigger canvas dimension updates
    setTimeout(() => {
      viewer.onResize();
      schematic2D.onResize();
    }, 60);
  }

  btnViewSplit?.addEventListener('click', () => setViewMode('split'));
  btnView3D?.addEventListener('click', () => setViewMode('3d'));
  btnView2D?.addEventListener('click', () => setViewMode('2d'));

  let eventSource = null;
  let isConnected = false;

  function connectEventStream() {
    console.log('[MoveAssist] Connecting to real-time telemetry stream...');
    eventSource = new EventSource('/api/stream');

    eventSource.onopen = () => {
      isConnected = true;
      console.log('[MoveAssist] Telemetry stream connected (SSE 60Hz)');
    };

    eventSource.onmessage = (event) => {
      try {
        const telemetry = JSON.parse(event.data);
        try { viewer.updateTelemetry(telemetry); } catch (e) { console.warn('Viewer update error:', e); }
        try { schematic2D.update(telemetry); } catch (e) { console.warn('Schematic update error:', e); }
        try { charts.update(telemetry); } catch (e) { console.warn('Charts update error:', e); }
        try { dashboard.update(telemetry); } catch (e) { console.warn('Dashboard update error:', e); }
      } catch (err) {
        console.error('[MoveAssist] Telemetry parsing error:', err);
      }
    };

    eventSource.onerror = (err) => {
      console.warn('[MoveAssist] Stream interrupted, falling back to polling...', err);
      eventSource.close();
      isConnected = false;
      setTimeout(startPollingFallback, 1000);
    };
  }

  function startPollingFallback() {
    if (isConnected) return;
    const interval = setInterval(async () => {
      if (isConnected) {
        clearInterval(interval);
        return;
      }
      try {
        const resp = await fetch('/api/state');
        if (resp.ok) {
          const telemetry = await resp.json();
          try { viewer.updateTelemetry(telemetry); } catch (e) { console.warn('Viewer polling error:', e); }
          try { schematic2D.update(telemetry); } catch (e) { console.warn('Schematic polling error:', e); }
          try { charts.update(telemetry); } catch (e) { console.warn('Charts polling error:', e); }
          try { dashboard.update(telemetry); } catch (e) { console.warn('Dashboard polling error:', e); }
        }
      } catch (e) {
        // Retry SSE reconnection every 5s
        connectEventStream();
        clearInterval(interval);
      }
    }, 50); // 20 Hz polling fallback
  }

  // Start Real-Time Stream
  connectEventStream();
});

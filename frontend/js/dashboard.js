/**
 * MoveAssist Interactive Dashboard & Telemetry Manager
 * SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
 */

class MoveAssistDashboard {
  constructor(viewer, charts) {
    this.viewer = viewer;
    this.charts = charts;

    // DOM Element References
    this.modeBadge = document.getElementById('safety-mode-badge');
    this.gaitPhaseBadge = document.getElementById('gait-phase-badge');
    this.strideCountEl = document.getElementById('stride-count');
    this.motorTempEl = document.getElementById('motor-temp');
    
    // Actuator HUD Ring
    this.hudRingFill = document.getElementById('hud-ring-fill');
    this.hudCenterVal = document.getElementById('hud-center-val');
    this.hudTorqueVal = document.getElementById('hud-torque-val');

    // Demo elements
    this.demoBtn = document.getElementById('btn-start-demo');
    this.demoNarrative = document.getElementById('demo-narrative-text');
    this.demoSteps = [
      document.getElementById('demo-step-1'),
      document.getElementById('demo-step-2'),
      document.getElementById('demo-step-3'),
      document.getElementById('demo-step-4'),
      document.getElementById('demo-step-5')
    ];

    // E-Stop & Safety elements
    this.estopBtn = document.getElementById('btn-estop');
    this.resetEstopBtn = document.getElementById('btn-reset-estop');
    this.alertsBox = document.getElementById('safety-alerts-box');

    // Controls
    this.strengthSlider = document.getElementById('slider-strength');
    this.strengthVal = document.getElementById('val-strength');
    this.fatigueSlider = document.getElementById('slider-fatigue');
    this.fatigueVal = document.getElementById('val-fatigue');

    // Anthropometrics
    this.inputHeight = document.getElementById('input-height');
    this.inputMass = document.getElementById('input-mass');
    this.btnUpdateAnthro = document.getElementById('btn-update-anthro');
    this.btnCalibrate = document.getElementById('btn-calibrate');
    this.calStatusText = document.getElementById('cal-status-text');

    // Report Download Elements
    this.recBadge = document.getElementById('recording-badge');
    this.recCounter = document.getElementById('report-samples-counter');
    this.downloadExcelBtn = document.getElementById('btn-download-excel');

    // Controlled Soft Stop Elements
    this.btnSoftStop = document.getElementById('btn-soft-stop');
    this.selectSoftStopDuration = document.getElementById('select-soft-stop-duration');
    this.softStopHud = document.getElementById('soft-stop-hud');
    this.softStopTimer = document.getElementById('soft-stop-timer');
    this.softStopProgressBar = document.getElementById('soft-stop-progress-bar');
    this.softStopCadenceScale = document.getElementById('soft-stop-cadence-scale');
    this.softStopSeriousness = document.getElementById('soft-stop-seriousness');
    this.softStopEscalationNote = document.getElementById('soft-stop-escalation-note');
    this.btnTestFatigueFall = document.getElementById('btn-test-fatigue-fall');
    this.btnTestFatigueFallAcute = document.getElementById('btn-test-fatigue-fall-acute');

    // Sensor Matrix Readouts
    // Sensor Matrix Readouts
    this.imuThighPitch = document.getElementById('sensor-thigh-pitch');
    this.imuShankPitch = document.getElementById('sensor-shank-pitch');
    this.encoderAngle = document.getElementById('sensor-encoder-angle');
    this.fsrTotalGrf = document.getElementById('sensor-fsr-grf');
    this.emgEnvelope = document.getElementById('sensor-emg-env');

    // Kinematic Movement Modes & Jog Elements
    this.modeBtns = document.querySelectorAll('.mode-btn');
    this.jogSliderWrap = document.getElementById('jog-slider-wrap');
    this.jogSlider = document.getElementById('slider-manual-jog');
    this.jogVal = document.getElementById('val-manual-jog');

    // Biomechanical Assistance & Power Elements
    this.humanStrengthPct = document.getElementById('val-human-strength-pct');
    this.humanTorqueNm = document.getElementById('val-human-torque-nm');
    this.exoStrengthPct = document.getElementById('val-exo-strength-pct');
    this.exoTorqueNm = document.getElementById('val-exo-torque-nm');
    this.barHumanEffort = document.getElementById('bar-human-effort');
    this.barExoEffort = document.getElementById('bar-exo-effort');
    this.assistSummaryBadge = document.getElementById('assist-mode-summary');

    this.mechPowerVal = document.getElementById('val-mech-power');
    this.elecPowerVal = document.getElementById('val-elec-power');
    this.peakPowerVal = document.getElementById('val-peak-power');
    this.cumEnergyVal = document.getElementById('val-cumulative-energy');
    this.actuatorLoadBadge = document.getElementById('actuator-load-badge');

    this.bindEvents();
  }

  bindEvents() {
    // 0. Kinematic Movement Modes
    this.modeBtns?.forEach(btn => {
      btn.addEventListener('click', () => {
        const mode = btn.getAttribute('data-mode') || 'WALK';
        const jogAngle = parseFloat(this.jogSlider?.value || '0');
        fetch('/api/kinematics/mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: mode, jog_angle_deg: jogAngle })
        });
        this.modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        if (this.jogSliderWrap) {
          this.jogSliderWrap.style.display = (mode === 'MANUAL_JOG') ? 'flex' : 'none';
        }
      });
    });

    // Manual Jog Slider
    if (this.jogSlider) {
      this.jogSlider.addEventListener('input', (e) => {
        const angle = parseFloat(e.target.value);
        if (this.jogVal) this.jogVal.textContent = angle.toFixed(1) + '°';
        fetch('/api/kinematics/mode', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ mode: 'MANUAL_JOG', jog_angle_deg: angle })
        });
      });
    }

    // 1. Demonstration Button
    this.demoBtn.addEventListener('click', () => {
      const isRunning = this.demoBtn.classList.contains('active-demo');
      if (isRunning) {
        fetch('/api/demo/stop', { method: 'POST' });
        this.demoBtn.classList.remove('active-demo');
        this.demoBtn.innerHTML = `<span>▶</span> START DEMONSTRATION`;
      } else {
        fetch('/api/demo/start', { method: 'POST' });
        this.demoBtn.classList.add('active-demo');
        this.demoBtn.innerHTML = `<span>⏸</span> PAUSE DEMONSTRATION`;
      }
    });

    // 2. Emergency Stop & Controlled Soft Stop Buttons
    this.estopBtn.addEventListener('click', () => {
      fetch('/api/safety/estop', { method: 'POST' });
    });

    this.btnSoftStop?.addEventListener('click', () => {
      const dur = parseFloat(this.selectSoftStopDuration?.value || '90');
      fetch('/api/safety/soft_stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ duration_s: dur, reason: 'MANUAL_CONTROLLED_SOFT_STOP' })
      });
    });

    this.btnTestFatigueFall?.addEventListener('click', () => {
      this.fatigueSlider.value = 0.88;
      this.fatigueVal.textContent = '88%';
      fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fatigue: 0.88 })
      });
    });

    this.btnTestFatigueFallAcute?.addEventListener('click', () => {
      this.fatigueSlider.value = 0.96;
      this.fatigueVal.textContent = '96%';
      fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fatigue: 0.96 })
      });
    });

    this.resetEstopBtn.addEventListener('click', () => {
      fetch('/api/safety/reset', { method: 'POST' });
    });

    // 3. Sensor Fault Buttons
    document.getElementById('btn-fault-imu')?.addEventListener('click', () => {
      fetch('/api/fault/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor: 'IMU' })
      });
    });

    document.getElementById('btn-fault-fsr')?.addEventListener('click', () => {
      fetch('/api/fault/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor: 'FSR' })
      });
    });

    document.getElementById('btn-fault-encoder')?.addEventListener('click', () => {
      fetch('/api/fault/inject', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ sensor: 'ENCODER' })
      });
    });

    document.getElementById('btn-clear-faults')?.addEventListener('click', () => {
      fetch('/api/fault/clear', { method: 'POST' });
    });

    // 4. Sliders (Manual Overrides)
    this.strengthSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      this.strengthVal.textContent = Math.round(val * 100) + '%';
      fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ strength: val })
      });
    });

    this.fatigueSlider.addEventListener('input', (e) => {
      const val = parseFloat(e.target.value);
      this.fatigueVal.textContent = Math.round(val * 100) + '%';
      fetch('/api/control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fatigue: val })
      });
    });

    // 5. Anthropometrics
    this.btnUpdateAnthro.addEventListener('click', () => {
      const h = parseFloat(this.inputHeight.value);
      const m = parseFloat(this.inputMass.value);
      fetch('/api/anthropometrics', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ height_m: h, mass_kg: m })
      });
    });

    this.btnCalibrate.addEventListener('click', () => {
      fetch('/api/calibrate', { method: 'POST' });
      this.calStatusText.textContent = "Calibrating: ZEROING...";
    });

    // 6. Viewport Layer Toggles & Camera
    document.getElementById('btn-reset-cam')?.addEventListener('click', () => {
      this.viewer.resetCamera();
    });

    document.getElementById('btn-toggle-exo')?.addEventListener('click', (e) => {
      const active = e.target.classList.toggle('active');
      this.viewer.toggleLayer('exo', active);
    });

    document.getElementById('btn-toggle-anatomy')?.addEventListener('click', (e) => {
      const active = e.target.classList.toggle('active');
      this.viewer.toggleLayer('anatomy', active);
    });

    document.getElementById('btn-toggle-sensors')?.addEventListener('click', (e) => {
      const active = e.target.classList.toggle('active');
      this.viewer.toggleLayer('sensors', active);
    });
  }

  update(telemetry) {
    if (!telemetry) return;

    // 1. Safety Mode Badge
    const safety = telemetry.safety || {};
    const mode = safety.mode || 'NORMAL_AAN';
    this.modeBadge.className = 'status-badge';

    if (mode === 'NORMAL_AAN') {
      this.modeBadge.classList.add('badge-normal');
      this.modeBadge.innerHTML = `<span class="pulse-dot"></span> NORMAL AAN`;
      this.estopBtn.classList.remove('latched');
      this.btnSoftStop?.classList.remove('active-soft');
      if (this.softStopHud) this.softStopHud.style.display = 'none';
    } else if (mode === 'CONTROLLED_SOFT_STOP') {
      this.modeBadge.classList.add('badge-soft-stop');
      this.modeBadge.innerHTML = `<span class="pulse-dot"></span> SOFT STOP (ANTI-FALL)`;
      this.estopBtn.classList.remove('latched');
      this.btnSoftStop?.classList.add('active-soft');
      if (this.softStopHud) {
        this.softStopHud.style.display = 'flex';
        const css = safety.controlled_soft_stop || {};
        const rem = Math.max(0, Math.round(css.remaining_s || 0));
        const mins = Math.floor(rem / 60);
        const secs = rem % 60;
        if (this.softStopTimer) {
          this.softStopTimer.textContent = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        }
        if (this.softStopProgressBar) {
          this.softStopProgressBar.style.width = `${css.progress_pct || 0}%`;
        }
        if (this.softStopCadenceScale) {
          this.softStopCadenceScale.textContent = `${Math.round((css.velocity_scale || 0) * 100)}%`;
        }

        // Seriousness badge & dynamic update indicator
        const seriousness = css.fall_seriousness || safety.fall_seriousness || 'NORMAL';
        if (this.softStopSeriousness) {
          if (seriousness === 'ACUTE_IMMEDIATE_FALL') {
            this.softStopSeriousness.textContent = 'ACUTE (30s)';
            this.softStopSeriousness.style.background = 'rgba(244,63,94,0.2)';
            this.softStopSeriousness.style.borderColor = 'rgba(244,63,94,0.5)';
            this.softStopSeriousness.style.color = '#f43f5e';
          } else if (seriousness === 'HIGH') {
            this.softStopSeriousness.textContent = 'HIGH (60s)';
            this.softStopSeriousness.style.background = 'rgba(251,146,60,0.2)';
            this.softStopSeriousness.style.borderColor = 'rgba(251,146,60,0.5)';
            this.softStopSeriousness.style.color = '#fb923c';
          } else if (seriousness === 'ELEVATED') {
            this.softStopSeriousness.textContent = 'ELEVATED (90s)';
            this.softStopSeriousness.style.background = 'rgba(251,191,36,0.2)';
            this.softStopSeriousness.style.borderColor = 'rgba(251,191,36,0.5)';
            this.softStopSeriousness.style.color = '#fbbf24';
          } else {
            this.softStopSeriousness.textContent = `${Math.round(css.duration_s || 90)}s SET`;
            this.softStopSeriousness.style.background = 'rgba(56,189,248,0.2)';
            this.softStopSeriousness.style.borderColor = 'rgba(56,189,248,0.5)';
            this.softStopSeriousness.style.color = '#38bdf8';
          }
        }

        // Show escalation banner if timer was shortened to 30s
        if (this.softStopEscalationNote) {
          if (css.duration_s <= 35.0 || seriousness === 'ACUTE_IMMEDIATE_FALL' || (css.reason && css.reason.includes('ESCALATION'))) {
            this.softStopEscalationNote.style.display = 'block';
            const fatiguePct = Math.round((telemetry.user?.fatigue_index || 0.96) * 100);
            this.softStopEscalationNote.textContent = `⚡ ACUTE FALL RISK (${fatiguePct}%): Rapid 30s Anti-Buckle Deceleration Engaged!`;
          } else {
            this.softStopEscalationNote.style.display = 'none';
          }
        }
      }
    } else if (mode === 'PROTECTIVE_MODE') {
      this.modeBadge.classList.add('badge-protective');
      this.modeBadge.innerHTML = `<span class="pulse-dot"></span> PROTECTIVE MODE`;
      this.estopBtn.classList.remove('latched');
      this.btnSoftStop?.classList.remove('active-soft');
      if (this.softStopHud) this.softStopHud.style.display = 'none';
    } else if (mode === 'SAFE_FALLBACK') {
      this.modeBadge.classList.add('badge-fallback');
      this.modeBadge.innerHTML = `<span class="pulse-dot"></span> SAFE FALLBACK`;
      this.estopBtn.classList.remove('latched');
      this.btnSoftStop?.classList.remove('active-soft');
      if (this.softStopHud) this.softStopHud.style.display = 'none';
    } else if (mode === 'EMERGENCY_STOP') {
      this.modeBadge.classList.add('badge-estop');
      this.modeBadge.innerHTML = `<span class="pulse-dot"></span> EMERGENCY STOP`;
      this.estopBtn.classList.add('latched');
      this.btnSoftStop?.classList.remove('active-soft');
      if (this.softStopHud) this.softStopHud.style.display = 'none';
    }

    // 2. Gait Phase & Stride Count
    const gait = telemetry.gait || {};
    if (this.gaitPhaseBadge) {
      this.gaitPhaseBadge.textContent = (gait.phase || 'STANCE').replace('_', ' ');
    }
    if (this.strideCountEl) {
      this.strideCountEl.textContent = gait.stride_count || 0;
    }

    // 3. Actuator HUD Ring
    const torques = telemetry.torques || {};
    const cmdTorque = Math.abs(torques.commanded_nm || 0);
    const maxTorque = 35.0;
    const ratio = Math.min(1.0, cmdTorque / maxTorque);
    const circumference = 2 * Math.PI * 22; // r=22
    const offset = circumference * (1.0 - ratio);

    if (this.hudRingFill) {
      this.hudRingFill.style.strokeDasharray = circumference;
      this.hudRingFill.style.strokeDashoffset = offset;
      // Change color according to mode / torque
      if (mode === 'EMERGENCY_STOP') {
        this.hudRingFill.style.stroke = '#f43f5e';
      } else if (mode === 'PROTECTIVE_MODE') {
        this.hudRingFill.style.stroke = '#8b5cf6';
      } else if (cmdTorque > 25.0) {
        this.hudRingFill.style.stroke = '#f59e0b';
      } else {
        this.hudRingFill.style.stroke = '#06b6d4';
      }
    }
    if (this.hudCenterVal) {
      this.hudCenterVal.textContent = Math.round(ratio * 100) + '%';
    }
    if (this.hudTorqueVal) {
      this.hudTorqueVal.textContent = (torques.commanded_nm || 0).toFixed(1) + ' Nm';
    }

    // 4. Motor Temp
    if (this.motorTempEl) {
      this.motorTempEl.textContent = (telemetry.actuator?.motor_temp_c || 32.0).toFixed(1) + '°C';
    }

    // 5. Automated Demo Pipeline
    const demo = telemetry.demo || {};
    if (demo.active) {
      this.demoBtn.classList.add('active-demo');
      this.demoBtn.innerHTML = `<span>⏹</span> STOP DEMO (P${demo.phase})`;
      this.demoNarrative.textContent = demo.description || '';

      const pIndex = (demo.phase || 1) - 1;
      this.demoSteps.forEach((stepEl, idx) => {
        if (!stepEl) return;
        stepEl.className = 'step-chip';
        if (idx < pIndex) stepEl.classList.add('completed');
        else if (idx === pIndex) stepEl.classList.add('active');
      });

      // Synchronize slider handles to show live adaptation
      this.strengthSlider.value = demo.target_strength;
      this.strengthVal.textContent = Math.round(demo.target_strength * 100) + '%';
      this.fatigueSlider.value = demo.target_fatigue;
      this.fatigueVal.textContent = Math.round(demo.target_fatigue * 100) + '%';
    } else {
      this.demoBtn.classList.remove('active-demo');
      this.demoBtn.innerHTML = `<span>▶</span> START DEMONSTRATION`;
      this.demoSteps.forEach(s => s && (s.className = 'step-chip'));
    }

    // 6. Safety Alerts Box
    if (this.alertsBox && safety.alerts) {
      if (safety.alerts.length === 0) {
        this.alertsBox.innerHTML = `<span style="color:#64748b">All systems nominal. Multi-tier safety supervision active.</span>`;
      } else {
        this.alertsBox.innerHTML = safety.alerts.map(a => {
          let cls = 'LIMIT';
          if (a.startsWith('CRITICAL')) cls = 'CRITICAL';
          else if (a.startsWith('WARN')) cls = 'WARN';
          return `<div class="alert-entry ${cls}">⚠️ ${a}</div>`;
        }).join('');
      }
    }

    // 7. Virtual Sensor Matrix Readouts
    const sensors = telemetry.sensors || {};
    if (this.imuThighPitch && sensors.imu_thigh) {
      this.imuThighPitch.textContent = (sensors.imu_thigh.pitch_deg || 0).toFixed(1) + '°';
    }
    if (this.imuShankPitch && sensors.imu_shank) {
      this.imuShankPitch.textContent = (sensors.imu_shank.pitch_deg || 0).toFixed(1) + '°';
    }
    if (this.encoderAngle && sensors.encoder) {
      this.encoderAngle.textContent = (sensors.encoder.angle_deg || 0).toFixed(1) + '°';
    }
    if (this.fsrTotalGrf && sensors.foot_pressure) {
      this.fsrTotalGrf.textContent = (sensors.foot_pressure.total_grf_n || 0).toFixed(0) + ' N';
    }
    if (this.emgEnvelope && sensors.emg) {
      this.emgEnvelope.textContent = (sensors.emg.envelope_norm || 0).toFixed(2);
    }

    // 8. Anthropometrics status
    const anthro = telemetry.anthropometry || {};
    if (this.calStatusText && anthro.calibration_state) {
      this.calStatusText.textContent = `Status: ${anthro.calibration_state} (${anthro.calibration_progress}%)`;
    }
    document.getElementById('stat-distal-mass') && (document.getElementById('stat-distal-mass').textContent = (anthro.total_distal_mass_kg || 4.39) + ' kg');
    document.getElementById('stat-knee-moi') && (document.getElementById('stat-knee-moi').textContent = (anthro.I_knee_total_kgm2 || 0.38).toFixed(3) + ' kg·m²');

    // 9. Clinical Report Status
    const reportStatus = telemetry.report_status || {};
    if (this.recBadge) {
      if (reportStatus.is_recording) {
        this.recBadge.style.display = 'flex';
        this.downloadExcelBtn?.classList.remove('ready-pulse');
        if (this.recCounter) {
          this.recCounter.textContent = `Recording: ${reportStatus.recorded_samples || 0} samples`;
        }
      } else {
        this.recBadge.style.display = 'none';
        if (reportStatus.has_trial_data) {
          this.downloadExcelBtn?.classList.add('ready-pulse');
          if (this.recCounter) {
            this.recCounter.textContent = `Trial ready (${reportStatus.recorded_samples || 0} samples)`;
          }
        } else if (this.recCounter) {
          this.recCounter.textContent = `Session buffer (${reportStatus.rolling_samples || 0} samples)`;
        }
      }
    }

    // 10. Kinematic Movement Modes State Synchronization
    const k = telemetry.kinematics || {};
    const currentMode = (k.mode || 'WALK').toUpperCase().replace('-', '_');
    this.modeBtns?.forEach(btn => {
      const bMode = (btn.getAttribute('data-mode') || '').toUpperCase().replace('-', '_');
      if (bMode === currentMode) {
        btn.classList.add('active');
      } else {
        btn.classList.remove('active');
      }
    });

    if (this.jogSliderWrap) {
      this.jogSliderWrap.style.display = (currentMode === 'MANUAL_JOG') ? 'flex' : 'none';
      if (currentMode === 'MANUAL_JOG' && k.jog_angle_deg !== undefined) {
        if (this.jogSlider && document.activeElement !== this.jogSlider) {
          this.jogSlider.value = k.jog_angle_deg;
        }
        if (this.jogVal) {
          this.jogVal.textContent = k.jog_angle_deg.toFixed(1) + '°';
        }
      }
    }

    // 11. Biomechanical Assistance & Robotic Actuators Power Telemetry
    const p = telemetry.power || {};
    const humanPct = p.human_strength_used_pct ?? 50.0;
    const exoPct = p.exo_strength_used_pct ?? 50.0;
    const humanTorque = p.human_torque_nm ?? 0.0;
    const exoTorque = p.exo_torque_nm ?? 0.0;

    if (this.humanStrengthPct) this.humanStrengthPct.textContent = `${humanPct.toFixed(1)}%`;
    if (this.humanTorqueNm) this.humanTorqueNm.textContent = `(${humanTorque >= 0 ? '+' : ''}${humanTorque.toFixed(1)} Nm)`;
    if (this.exoStrengthPct) this.exoStrengthPct.textContent = `${exoPct.toFixed(1)}%`;
    if (this.exoTorqueNm) this.exoTorqueNm.textContent = `(${exoTorque >= 0 ? '+' : ''}${exoTorque.toFixed(1)} Nm)`;

    if (this.barHumanEffort) this.barHumanEffort.style.width = `${Math.max(2, Math.min(98, humanPct))}%`;
    if (this.barExoEffort) this.barExoEffort.style.width = `${Math.max(2, Math.min(98, exoPct))}%`;

    if (this.mechPowerVal) this.mechPowerVal.textContent = (p.mechanical_watts ?? 0.0).toFixed(1);
    if (this.elecPowerVal) this.elecPowerVal.textContent = (p.electrical_watts ?? 6.5).toFixed(1);
    if (this.peakPowerVal) this.peakPowerVal.textContent = (p.peak_watts ?? 0.0).toFixed(1);
    if (this.cumEnergyVal) this.cumEnergyVal.textContent = (p.cumulative_kj ?? 0.0).toFixed(3);
    if (this.actuatorLoadBadge) this.actuatorLoadBadge.textContent = `LOAD: ${(p.actuator_load_pct ?? 0.0).toFixed(1)}%`;
    if (this.assistSummaryBadge) {
      this.assistSummaryBadge.textContent = currentMode === 'STANDBY' ? 'STATIC HOLD' : (currentMode === 'MANUAL_JOG' ? 'MANUAL JOG' : 'AAN ADAPTIVE');
    }
  }
}

window.MoveAssistDashboard = MoveAssistDashboard;

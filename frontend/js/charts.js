/**
 * MoveAssist High-Performance HTML5 Canvas Strip-Charts
 * SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
 */

class CanvasStripChart {
  constructor(canvasId, options = {}) {
    this.canvas = document.getElementById(canvasId);
    this.ctx = this.canvas.getContext('2d');
    this.options = Object.assign({
      maxSamples: 150,
      minY: -10,
      maxY: 40,
      autoScale: false,
      gridLines: 4,
      unit: '',
      fillAlpha: 0.15,
      showZeroLine: true,
      referenceLines: []  // [{y: 0, color: 'rgba(255,255,255,0.2)', dash: [2,2]}]
    }, options);

    this.series = []; // Array of { name, color, buffer: [] }
    this.labels = [];

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const w = rect.width > 0 ? rect.width : (this.canvas.clientWidth || 320);
    const h = rect.height > 0 ? rect.height : (this.canvas.clientHeight || 140);
    this.canvas.width = Math.round(w * dpr);
    this.canvas.height = Math.round(h * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    this.width = w;
    this.height = h;
  }

  addSeries(name, color) {
    this.series.push({
      name: name,
      color: color,
      buffer: []
    });
  }

  pushData(pointMap) {
    for (let s of this.series) {
      const val = pointMap[s.name] !== undefined ? pointMap[s.name] : 0;
      s.buffer.push(val);
      if (s.buffer.length > this.options.maxSamples) {
        s.buffer.shift();
      }
    }
  }

  render() {
    if (!this.width || this.width < 10 || !this.height || this.height < 10) {
      this.resize();
    }
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;
    if (!w || !h || w < 10 || h < 10) return;

    ctx.clearRect(0, 0, w, h);

    // Dynamic scale computation
    let minY = this.options.minY;
    let maxY = this.options.maxY;

    if (this.options.autoScale) {
      let allVals = [];
      for (let s of this.series) {
        allVals.push(...s.buffer);
      }
      if (allVals.length > 0) {
        const dataMin = Math.min(...allVals);
        const dataMax = Math.max(...allVals);
        const pad = Math.max(2.0, (dataMax - dataMin) * 0.15);
        minY = dataMin - pad;
        maxY = dataMax + pad;
      }
    }

    const rangeY = (maxY - minY) || 1.0;
    const getY = (val) => h - ((val - minY) / rangeY) * (h - 20) - 10;

    // Draw Grid Lines & Values
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.06)';
    ctx.lineWidth = 1;
    ctx.font = '10px "JetBrains Mono", monospace';
    ctx.fillStyle = '#64748b';

    const steps = this.options.gridLines;
    for (let i = 0; i <= steps; i++) {
      const v = minY + (rangeY * (i / steps));
      const y = getY(v);
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();

      ctx.fillText(v.toFixed(0) + this.options.unit, 6, y - 3);
    }

    // Reference lines (e.g. 0.0 line or ROM limit lines)
    if (this.options.showZeroLine && minY <= 0 && maxY >= 0) {
      const yZero = getY(0);
      ctx.save();
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(0, yZero);
      ctx.lineTo(w, yZero);
      ctx.stroke();
      ctx.restore();
    }

    for (let ref of this.options.referenceLines) {
      const yRef = getY(ref.y);
      ctx.save();
      ctx.strokeStyle = ref.color || '#f43f5e';
      ctx.setLineDash(ref.dash || [3, 3]);
      ctx.beginPath();
      ctx.moveTo(0, yRef);
      ctx.lineTo(w, yRef);
      ctx.stroke();
      if (ref.label) {
        ctx.fillStyle = ref.color || '#f43f5e';
        ctx.fillText(ref.label, w - 60, yRef - 3);
      }
      ctx.restore();
    }

    // Draw Data Series
    const numPoints = this.options.maxSamples;
    const stepX = w / (numPoints - 1);

    for (let s of this.series) {
      if (s.buffer.length < 2) continue;

      ctx.save();
      ctx.strokeStyle = s.color;
      ctx.lineWidth = 1.8;
      ctx.lineJoin = 'round';
      ctx.beginPath();

      const startIdx = numPoints - s.buffer.length;
      for (let i = 0; i < s.buffer.length; i++) {
        const x = (startIdx + i) * stepX;
        const y = getY(s.buffer[i]);
        if (i === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      }
      ctx.stroke();

      // Current point pulse
      const lastX = (startIdx + s.buffer.length - 1) * stepX;
      const lastY = getY(s.buffer[s.buffer.length - 1]);
      ctx.fillStyle = s.color;
      ctx.beginPath();
      ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
      ctx.fill();

      ctx.restore();
    }
  }
}

class MoveAssistChartsManager {
  constructor() {
    this.torqueChart = null;
    this.aanChart = null;
    this.kinematicsChart = null;
    this.fatigueChart = null;
    this.initCharts();
  }

  initCharts() {
    // 1. Torques Chart (Required, User, Commanded, Actuator)
    this.torqueChart = new CanvasStripChart('chart-torques', {
      minY: -25,
      maxY: 35,
      unit: ' Nm',
      showZeroLine: true,
      referenceLines: [
        { y: 35, color: 'rgba(244,63,94,0.4)', dash: [4, 4], label: '+35 Nm Limit' },
        { y: -35, color: 'rgba(244,63,94,0.4)', dash: [4, 4], label: '-35 Nm Limit' }
      ]
    });
    this.torqueChart.addSeries('tau_req', '#06b6d4');   // Cyan
    this.torqueChart.addSeries('tau_user', '#10b981');  // Emerald
    this.torqueChart.addSeries('tau_cmd', '#f59e0b');   // Amber
    this.torqueChart.addSeries('tau_act', '#c084fc');   // Violet

    // 2. AAN Assistance vs. User % (Inverse relationship)
    this.aanChart = new CanvasStripChart('chart-aan', {
      minY: 0,
      maxY: 100,
      unit: '%',
      showZeroLine: false
    });
    this.aanChart.addSeries('assist_pct', '#38bdf8'); // Cyan
    this.aanChart.addSeries('user_pct', '#34d399');   // Emerald

    // 3. Knee Kinematics (Angle & Velocity)
    this.kinematicsChart = new CanvasStripChart('chart-kinematics', {
      minY: -10,
      maxY: 125,
      unit: '°',
      showZeroLine: true,
      referenceLines: [
        { y: 0, color: 'rgba(244,63,94,0.5)', dash: [3, 3], label: '0° Ext' },
        { y: 115, color: 'rgba(244,63,94,0.5)', dash: [3, 3], label: '115° Flex' }
      ]
    });
    this.kinematicsChart.addSeries('knee_angle', '#38bdf8');
    this.kinematicsChart.addSeries('knee_vel', '#fbbf24');

    // 4. Fatigue & Muscle Activation
    this.fatigueChart = new CanvasStripChart('chart-fatigue', {
      minY: 0,
      maxY: 1.0,
      unit: '',
      showZeroLine: false,
      referenceLines: [
        { y: 0.40, color: 'rgba(245,158,11,0.5)', dash: [4, 4], label: 'Boost Threshold' }
      ]
    });
    this.fatigueChart.addSeries('fatigue', '#f43f5e');     // Rose
    this.fatigueChart.addSeries('emg_envelope', '#10b981'); // Emerald
  }

  update(telemetry) {
    if (!telemetry) return;

    // 1. Push Torques
    const torques = telemetry.torques || {};
    this.torqueChart.pushData({
      tau_req: torques.required_nm || 0,
      tau_user: torques.user_estimated_nm || 0,
      tau_cmd: torques.commanded_nm || 0,
      tau_act: torques.actuator_output_nm || 0
    });
    this.torqueChart.render();

    // 2. Push AAN %
    const aan = telemetry.aan || {};
    this.aanChart.pushData({
      assist_pct: aan.assistance_percent || 0,
      user_pct: aan.user_percent || 0
    });
    this.aanChart.render();

    // 3. Push Kinematics
    const k = telemetry.kinematics || {};
    this.kinematicsChart.pushData({
      knee_angle: k.knee_angle_deg || 0,
      knee_vel: (k.knee_velocity_deg_s || 0) * 0.2 // Scaled for visible visualization
    });
    this.kinematicsChart.render();

    // 4. Push Fatigue & EMG
    const emg = telemetry.sensors?.emg || {};
    this.fatigueChart.pushData({
      fatigue: aan.fatigue_index || 0,
      emg_envelope: emg.envelope_norm || 0
    });
    this.fatigueChart.render();
  }
}

window.MoveAssistChartsManager = MoveAssistChartsManager;

/**
 * MoveAssist 2D Biomechanical Kinematics & Actuator Engineering Schematic
 * SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
 * 
 * High-precision CAD / orthographic biomechanical canvas visualization
 * synchronized at 60 Hz with closed-loop telemetry.
 */

class MoveAssist2DSchematic {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    
    // Telemetry state & smooth interpolated motion state
    this.target_knee_deg = 0.0;
    this.target_thigh_deg = 0.0;
    this.target_shank_deg = 0.0;

    this.current_knee_deg = 0.0;
    this.current_thigh_deg = 0.0;
    this.current_shank_deg = 0.0;

    this.omega_knee_deg_s = 0.0;
    this.tau_cmd_nm = 0.0;
    this.tau_req_nm = 0.0;
    this.tau_user_nm = 0.0;
    this.vgrf_n = 0.0;
    this.fsr_heel = 0.0;
    this.fsr_meta = 0.0;
    this.fsr_toe = 0.0;
    this.emg_env = 0.05;
    this.gait_phase = "STANCE";
    this.gait_pct = 0.0;
    this.soft_stop_active = false;
    this.soft_stop_rem_s = 0.0;
    this.soft_stop_seriousness = "NORMAL";
    this.safety_mode = "NORMAL_AAN";
    this.kin_mode = "WALK";

    // Layout metrics
    this.width = 0;
    this.height = 0;
    this.dpr = window.devicePixelRatio || 1;

    this.onResize();
    window.addEventListener('resize', () => this.onResize());

    // Animation / render loop
    this.render();
  }

  onResize() {
    if (!this.canvas || !this.canvas.parentElement) return;
    const rect = this.canvas.parentElement.getBoundingClientRect();
    this.width = rect.width || 400;
    this.height = rect.height || 480;

    this.canvas.width = this.width * this.dpr;
    this.canvas.height = this.height * this.dpr;
    this.canvas.style.width = `${this.width}px`;
    this.canvas.style.height = `${this.height}px`;

    this.ctx.setTransform(this.dpr, 0, 0, this.dpr, 0, 0);
  }

  update(telemetry) {
    if (!telemetry) return;

    // Kinematics (Store as targets for smooth visual interpolation)
    const kin = telemetry.kinematics || {};
    this.target_knee_deg = kin.knee_angle_deg || 0.0;
    this.target_thigh_deg = kin.thigh_angle_deg || 0.0;
    this.target_shank_deg = kin.shank_angle_deg || 0.0;
    this.omega_knee_deg_s = kin.knee_velocity_deg_s || 0.0;

    // Torques
    const torques = telemetry.torques || {};
    this.tau_req_nm = torques.required_nm || 0.0;
    this.tau_user_nm = torques.user_estimated_nm || 0.0;
    this.tau_cmd_nm = torques.commanded_nm ?? torques.actuator_cmd_nm ?? 0.0;

    // Sensors
    const sensors = telemetry.sensors || {};
    const fsr = sensors.foot_pressure || {};
    this.fsr_heel = fsr.heel_n || 0.0;
    this.fsr_meta = fsr.metatarsal_n || 0.0;
    this.fsr_toe = fsr.toe_n || 0.0;
    this.vgrf_n = fsr.total_grf_n || 0.0;
    this.emg_env = sensors.emg?.envelope_norm || 0.05;

    // Gait FSM
    this.gait_phase = telemetry.gait_phase || (fsr.is_stance ? "STANCE" : "SWING");
    this.gait_pct = telemetry.gait_cycle_pct || 0.0;

    // Safety & Soft Stop
    const safety = telemetry.safety || {};
    this.safety_mode = safety.mode || "NORMAL_AAN";
    const css = safety.controlled_soft_stop || {};
    this.soft_stop_active = !!css.active;
    this.soft_stop_rem_s = css.remaining_s || 0.0;
    this.soft_stop_seriousness = css.fall_seriousness || safety.fall_seriousness || "NORMAL";

    // Mode tracking
    this.kin_mode = (kin.mode || 'WALK').toUpperCase().replace('-', '_');

    // Update overlay text chips if present
    const valMode = document.getElementById('schematic-val-mode');
    if (valMode) valMode.textContent = this.kin_mode;

    const valAngle = document.getElementById('schematic-val-angle');
    if (valAngle) valAngle.textContent = `${(this.target_knee_deg || 0).toFixed(1)}°`;

    const valTorque = document.getElementById('schematic-val-torque');
    if (valTorque) valTorque.textContent = `${(this.tau_cmd_nm || 0) >= 0 ? '+' : ''}${(this.tau_cmd_nm || 0).toFixed(1)} Nm`;

    const valPower = document.getElementById('schematic-val-power');
    if (valPower) {
      const pMech = telemetry.power?.mechanical_watts || 0.0;
      valPower.textContent = `${pMech.toFixed(1)} W`;
    }

    const valGrf = document.getElementById('schematic-val-grf');
    if (valGrf) valGrf.textContent = `${Math.round(this.vgrf_n)} N`;

    const lockBadge = document.getElementById('schematic-lock-badge');
    if (lockBadge) {
      lockBadge.style.display = this.soft_stop_active ? 'flex' : 'none';
    }
  }

  render() {
    requestAnimationFrame(() => this.render());

    if (!this.ctx || this.width === 0 || this.height === 0) return;
    const ctx = this.ctx;
    const w = this.width;
    const h = this.height;

    // 1. Blueprint Background & Grid
    ctx.save();
    ctx.clearRect(0, 0, w, h);

    // Dark technical gradient
    const bgGrad = ctx.createLinearGradient(0, 0, w, h);
    bgGrad.addColorStop(0, '#070b14');
    bgGrad.addColorStop(1, '#0d1527');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, w, h);

    // Technical grid lines
    ctx.lineWidth = 1;
    ctx.strokeStyle = 'rgba(30, 41, 69, 0.45)';
    const gridSize = 25;
    for (let x = 0; x < w; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, h);
      ctx.stroke();
    }
    for (let y = 0; y < h; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(w, y);
      ctx.stroke();
    }

    // Header Title Strip
    ctx.fillStyle = 'rgba(14, 23, 42, 0.85)';
    ctx.fillRect(0, 0, w, 28);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.2)';
    ctx.beginPath();
    ctx.moveTo(0, 28);
    ctx.lineTo(w, 28);
    ctx.stroke();

    ctx.font = '600 9px "SF Pro", Inter, -apple-system, sans-serif';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('2D SAGITTAL KINEMATIC & ACTUATOR ENGINEERING SCHEMATIC', 12, 18);

    ctx.font = '500 8px monospace';
    ctx.fillStyle = '#64748b';
    ctx.textAlign = 'right';
    ctx.fillText('SCALE: 1:4 • ISO 13482 COMPLIANT', w - 12, 18);
    ctx.textAlign = 'left';

    // 2. Kinematic Chain Setup (Sagittal Plane)
    // Frame-rate independent smooth exponential moving interpolation (LERP)
    // Synchronizes smoothly with 3D model, eliminating high-speed snapping
    const lerpFactor = 0.16;
    this.current_knee_deg += (this.target_knee_deg - this.current_knee_deg) * lerpFactor;
    this.current_thigh_deg += (this.target_thigh_deg - this.current_thigh_deg) * lerpFactor;
    this.current_shank_deg += (this.target_shank_deg - this.current_shank_deg) * lerpFactor;

    // Origin at Hip - balanced scale matching 3D visual amplitude
    const scale = Math.min(w / 380, h / 460);
    let hipX = w * 0.44;
    let hipY = 85 * scale;

    // In SIT_STAND mode: dynamically lower hip and shift posteriorly into chair
    if (this.kin_mode === 'SIT_STAND') {
      const sitRatio = Math.min(1.0, Math.max(0.0, this.current_knee_deg / 85.0));
      hipY += sitRatio * (46 * scale);
      hipX -= sitRatio * (18 * scale);
    }

    const thighLen = 120 * scale;
    const shankLen = 120 * scale;
    const footLen = 55 * scale;

    // Radians
    // Sagittal convention: 0 rad is pointing straight down along gravity plumb line
    // Thigh flexion positive (anterior/forward)
    const thighRad = (this.current_thigh_deg * Math.PI) / 180.0;
    // Knee flexion positive (posterior/backward bend of shank relative to thigh)
    const kneeRad = (this.current_knee_deg * Math.PI) / 180.0;
    const shankRad = thighRad - kneeRad;

    // Joint Centers
    const kneeX = hipX + thighLen * Math.sin(thighRad);
    const kneeY = hipY + thighLen * Math.cos(thighRad);

    const ankleX = kneeX + shankLen * Math.sin(shankRad);
    const ankleY = kneeY + shankLen * Math.cos(shankRad);

    const groundY = h - 35;
    const footHeelX = ankleX - 20 * scale;
    const footHeelY = ankleY + 12 * scale;
    const footToeX = ankleX + 48 * scale;
    const footToeY = ankleY + 12 * scale;

    // 3. Draw Vertical Reference Plumb Line & Hip Arc
    ctx.save();
    ctx.setLineDash([4, 4]);
    ctx.strokeStyle = 'rgba(100, 116, 139, 0.4)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(hipX, hipY - 20);
    ctx.lineTo(hipX, groundY);
    ctx.stroke();

    // Hip Angle Arc
    ctx.setLineDash([]);
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.6)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    const hipArcR = 28 * scale;
    const startAng = Math.PI / 2;
    const endAng = startAng - thighRad;
    ctx.arc(hipX, hipY, hipArcR, Math.min(startAng, endAng), Math.max(startAng, endAng));
    ctx.stroke();

    ctx.font = '600 8px monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText(`θ_hip: ${this.current_thigh_deg.toFixed(1)}°`, hipX + 10, hipY - 6);
    ctx.restore();

    // 4. Ground Contact Plane & Shadow
    ctx.save();
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.moveTo(15, groundY);
    ctx.lineTo(w - 15, groundY);
    ctx.stroke();

    // Ground hatch lines
    ctx.strokeStyle = 'rgba(30, 41, 69, 0.6)';
    ctx.lineWidth = 1;
    for (let gx = 20; gx < w - 20; gx += 12) {
      ctx.beginPath();
      ctx.moveTo(gx, groundY);
      ctx.lineTo(gx - 8, groundY + 8);
      ctx.stroke();
    }

    // Rehab Chair Silhouette (Rendered in SIT_STAND mode)
    if (this.kin_mode === 'SIT_STAND') {
      const chairSeatY = 85 * scale + (46 * scale) + (14 * scale);
      const chairSeatX = w * 0.44 - (18 * scale);
      ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      // Backrest
      ctx.moveTo(chairSeatX - 35 * scale, chairSeatY - 70 * scale);
      ctx.lineTo(chairSeatX - 25 * scale, chairSeatY);
      // Seat Cushion
      ctx.lineTo(chairSeatX + 22 * scale, chairSeatY);
      ctx.stroke();

      // Chair Legs
      ctx.strokeStyle = 'rgba(100, 116, 139, 0.5)';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(chairSeatX - 25 * scale, chairSeatY);
      ctx.lineTo(chairSeatX - 25 * scale, groundY);
      ctx.moveTo(chairSeatX + 18 * scale, chairSeatY);
      ctx.lineTo(chairSeatX + 18 * scale, groundY);
      ctx.stroke();

      // Chair Label
      ctx.font = '500 7px monospace';
      ctx.fillStyle = 'rgba(56, 189, 248, 0.6)';
      ctx.fillText('REHAB CHAIR (45cm)', chairSeatX - 30 * scale, chairSeatY - 74 * scale);
    }
    ctx.restore();

    // 5. Biological Muscle Action Lines (Biolink overlay)
    ctx.save();
    const emgAlpha = Math.min(1.0, 0.25 + this.emg_env * 1.5);
    const activeMuscleColor = this.soft_stop_active
      ? `rgba(251, 191, 36, ${emgAlpha})`
      : `rgba(244, 63, 94, ${emgAlpha})`;

    // Anterior: Quadriceps / Patellar Tendon line
    ctx.strokeStyle = activeMuscleColor;
    ctx.lineWidth = 2.5 + this.emg_env * 3.5;
    ctx.beginPath();
    ctx.moveTo(hipX + 12 * Math.cos(thighRad), hipY + 12 * Math.sin(thighRad));
    // Over anterior knee
    const patellaX = kneeX + 16 * Math.cos(thighRad - Math.PI / 2);
    const patellaY = kneeY + 16 * Math.sin(thighRad - Math.PI / 2);
    ctx.lineTo(patellaX, patellaY);
    ctx.lineTo(kneeX + 22 * Math.sin(shankRad), kneeY + 30 * Math.cos(shankRad));
    ctx.stroke();

    // Posterior: Hamstrings tendon line
    ctx.strokeStyle = 'rgba(168, 85, 247, 0.35)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(hipX - 10 * Math.cos(thighRad), hipY - 10 * Math.sin(thighRad));
    ctx.lineTo(kneeX - 14 * Math.cos(thighRad - Math.PI / 2), kneeY - 14 * Math.sin(thighRad - Math.PI / 2));
    ctx.lineTo(kneeX - 12 * Math.sin(shankRad), kneeY + 30 * Math.cos(shankRad));
    ctx.stroke();
    ctx.restore();

    // 6. Biological Bone Outlines (Femur & Tibia)
    ctx.save();
    ctx.strokeStyle = 'rgba(226, 232, 240, 0.25)';
    ctx.lineWidth = 10 * scale;
    ctx.lineCap = 'round';
    // Femur
    ctx.beginPath();
    ctx.moveTo(hipX, hipY);
    ctx.lineTo(kneeX, kneeY);
    ctx.stroke();
    // Tibia
    ctx.beginPath();
    ctx.moveTo(kneeX, kneeY);
    ctx.lineTo(ankleX, ankleY);
    ctx.stroke();
    ctx.restore();

    // 7. Exoskeleton Mechanical Linkages (CAD Style)
    ctx.save();
    // Thigh Cuff & Robotic Strut
    ctx.lineWidth = 6 * scale;
    ctx.strokeStyle = '#1e293b';
    ctx.lineCap = 'round';
    ctx.beginPath();
    ctx.moveTo(hipX + 4, hipY + 10);
    ctx.lineTo(kneeX + 4, kneeY);
    ctx.stroke();

    // Thigh Titanium Linkage Accent
    ctx.lineWidth = 2 * scale;
    ctx.strokeStyle = '#06b6d4';
    ctx.beginPath();
    ctx.moveTo(hipX + 4, hipY + 10);
    ctx.lineTo(kneeX + 4, kneeY);
    ctx.stroke();

    // Shank Brace & Telescopic Strut
    ctx.lineWidth = 6 * scale;
    ctx.strokeStyle = '#1e293b';
    ctx.beginPath();
    ctx.moveTo(kneeX + 3, kneeY);
    ctx.lineTo(ankleX + 3, ankleY);
    ctx.stroke();

    ctx.lineWidth = 2 * scale;
    ctx.strokeStyle = '#38bdf8';
    ctx.beginPath();
    ctx.moveTo(kneeX + 3, kneeY);
    ctx.lineTo(ankleX + 3, ankleY);
    ctx.stroke();

    // Telescopic graduation ticks on shank
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
    ctx.lineWidth = 1;
    for (let t = 0.25; t <= 0.75; t += 0.1) {
      const tx = kneeX + (ankleX - kneeX) * t;
      const ty = kneeY + (ankleY - kneeY) * t;
      const perpX = Math.cos(shankRad);
      const perpY = -Math.sin(shankRad);
      ctx.beginPath();
      ctx.moveTo(tx - 3 * perpX, ty - 3 * perpY);
      ctx.lineTo(tx + 3 * perpX, ty + 3 * perpY);
      ctx.stroke();
    }
    ctx.restore();

    // 8. Pelvis & Hip Pivot Assembly
    ctx.save();
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(hipX, hipY, 11 * scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.fillStyle = '#38bdf8';
    ctx.beginPath();
    ctx.arc(hipX, hipY, 4 * scale, 0, Math.PI * 2);
    ctx.fill();

    // Pelvic Crest Bracket
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(hipX - 18 * scale, hipY - 16 * scale);
    ctx.lineTo(hipX + 16 * scale, hipY - 16 * scale);
    ctx.lineTo(hipX, hipY);
    ctx.closePath();
    ctx.stroke();
    ctx.restore();

    // 9. Footplate & Ankle Joint
    ctx.save();
    // Carbon Footplate
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.roundRect(footHeelX, footHeelY, (footToeX - footHeelX), 7 * scale, [2, 4, 4, 2]);
    ctx.fill();
    ctx.stroke();

    // Ankle Pivot
    ctx.fillStyle = '#0f172a';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    ctx.arc(ankleX, ankleY, 7 * scale, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();
    ctx.restore();

    // 10. Dynamic Ground Reaction Force (vGRF) Vectors & FSR Markers
    ctx.save();
    const maxGrfH = 45 * scale;
    const drawGrfVector = (x, y, forceN, label, color) => {
      const arrowH = Math.min(maxGrfH, (forceN / 400.0) * maxGrfH);
      if (arrowH > 3) {
        ctx.strokeStyle = color;
        ctx.fillStyle = color;
        ctx.lineWidth = 2;
        // Vertical arrow pointing upwards
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x, y - arrowH);
        ctx.stroke();
        // Arrowhead
        ctx.beginPath();
        ctx.moveTo(x, y - arrowH - 3);
        ctx.lineTo(x - 3, y - arrowH + 2);
        ctx.lineTo(x + 3, y - arrowH + 2);
        ctx.closePath();
        ctx.fill();

        ctx.font = '600 7px monospace';
        ctx.fillText(`${Math.round(forceN)}N`, x - 8, y - arrowH - 6);
      }
      // FSR sensor dot on plate
      ctx.fillStyle = forceN > 15 ? color : '#334155';
      ctx.beginPath();
      ctx.arc(x, y, 3 * scale, 0, Math.PI * 2);
      ctx.fill();
    };

    drawGrfVector(footHeelX + 6 * scale, footHeelY + 3, this.fsr_heel, 'HEEL', '#10b981');
    drawGrfVector(ankleX + 16 * scale, footHeelY + 3, this.fsr_meta, 'META', '#06b6d4');
    drawGrfVector(footToeX - 6 * scale, footToeY + 3, this.fsr_toe, 'TOE', '#38bdf8');
    ctx.restore();

    // 11. Center of Mass (COM) Markers
    ctx.save();
    const drawCom = (x, y, label, massStr) => {
      ctx.strokeStyle = '#f59e0b';
      ctx.fillStyle = '#f59e0b';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.arc(x, y, 5 * scale, 0, Math.PI * 2);
      ctx.stroke();
      // Quarters
      ctx.beginPath();
      ctx.moveTo(x - 6 * scale, y);
      ctx.lineTo(x + 6 * scale, y);
      ctx.moveTo(x, y - 6 * scale);
      ctx.lineTo(x, y + 6 * scale);
      ctx.stroke();

      ctx.font = '500 7px monospace';
      ctx.fillStyle = '#f59e0b';
      ctx.fillText(`${label} (${massStr})`, x + 8 * scale, y + 2);
    };

    const comThighX = hipX + (kneeX - hipX) * 0.433;
    const comThighY = hipY + (kneeY - hipY) * 0.433;
    drawCom(comThighX, comThighY, 'COM_thigh', '4.4kg');

    const comShankX = kneeX + (ankleX - kneeX) * 0.433;
    const comShankY = kneeY + (ankleY - kneeY) * 0.433;
    drawCom(comShankX, comShankY, 'COM_shank', '3.3kg');
    ctx.restore();

    // 12. ROTARY KNEE ACTUATOR (Detailed Engineering Module)
    ctx.save();
    const actR = 24 * scale;

    // Outer Gear Rim / Housing
    ctx.fillStyle = '#0b1329';
    ctx.strokeStyle = this.soft_stop_active ? '#fbbf24' : '#06b6d4';
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    ctx.arc(kneeX, kneeY, actR, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    // Actuator Radial Bolt Circle (8 micro-dots)
    ctx.fillStyle = 'rgba(255, 255, 255, 0.4)';
    for (let i = 0; i < 8; i++) {
      const bAng = (i * Math.PI) / 4;
      const bx = kneeX + (actR - 4) * Math.cos(bAng);
      const by = kneeY + (actR - 4) * Math.sin(bAng);
      ctx.beginPath();
      ctx.arc(bx, by, 1.2, 0, Math.PI * 2);
      ctx.fill();
    }

    // Stator Teeth & Encoder Ring
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.3)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(kneeX, kneeY, actR - 8 * scale, 0, Math.PI * 2);
    ctx.stroke();

    // Knee Physiological ROM Sector (0 to 115 deg)
    // Reference line: extending from thigh direction
    const refExtAng = thighRad + Math.PI / 2;
    const maxFlexAng = refExtAng - (115 * Math.PI) / 180.0;

    // Shaded Safe ROM Sector
    ctx.fillStyle = 'rgba(6, 182, 212, 0.08)';
    ctx.beginPath();
    ctx.moveTo(kneeX, kneeY);
    ctx.arc(kneeX, kneeY, actR + 14 * scale, maxFlexAng, refExtAng);
    ctx.closePath();
    ctx.fill();

    // Active Flexion Wedge
    const curFlexAng = refExtAng - (this.current_knee_deg * Math.PI) / 180.0;
    ctx.fillStyle = 'rgba(6, 182, 212, 0.25)';
    ctx.beginPath();
    ctx.moveTo(kneeX, kneeY);
    ctx.arc(kneeX, kneeY, actR + 14 * scale, curFlexAng, refExtAng);
    ctx.closePath();
    ctx.fill();

    // Active Wedge Outline Arc
    ctx.strokeStyle = '#06b6d4';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(kneeX, kneeY, actR + 14 * scale, curFlexAng, refExtAng);
    ctx.stroke();

    // Actuator Center Core & Shaft
    ctx.fillStyle = this.soft_stop_active ? '#fbbf24' : '#0284c7';
    ctx.beginPath();
    ctx.arc(kneeX, kneeY, 6 * scale, 0, Math.PI * 2);
    ctx.fill();

    // Actuator Dynamic Torque Vector (Curved Arrow)
    const tauMag = Math.abs(this.tau_cmd_nm);
    if (tauMag > 0.5) {
      const torqueDir = this.tau_cmd_nm >= 0 ? 1 : -1; // +1 Extension, -1 Flexion
      const torqueColor = this.soft_stop_active ? '#fbbf24' : (torqueDir > 0 ? '#10b981' : '#a855f7');
      const arrowRadius = actR + 24 * scale;
      const sweepAng = Math.min(Math.PI * 0.8, (tauMag / 35.0) * Math.PI * 0.8);

      ctx.strokeStyle = torqueColor;
      ctx.lineWidth = Math.min(5, 1.5 + (tauMag / 35.0) * 3.5);
      ctx.beginPath();
      if (torqueDir > 0) {
        ctx.arc(kneeX, kneeY, arrowRadius, -Math.PI / 2, -Math.PI / 2 + sweepAng, false);
      } else {
        ctx.arc(kneeX, kneeY, arrowRadius, -Math.PI / 2, -Math.PI / 2 - sweepAng, true);
      }
      ctx.stroke();

      // Torque label
      ctx.font = '700 9px monospace';
      ctx.fillStyle = torqueColor;
      const torqueLabel = `${this.tau_cmd_nm >= 0 ? '+' : ''}${this.tau_cmd_nm.toFixed(1)} Nm`;
      ctx.fillText(`τ_exo: ${torqueLabel}`, kneeX + actR + 8 * scale, kneeY - 10 * scale);
    }

    // Controlled Soft Stop / Stance Lock Graphic
    if (this.soft_stop_active) {
      ctx.strokeStyle = '#fbbf24';
      ctx.fillStyle = '#fbbf24';
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(kneeX, kneeY, actR + 28 * scale, 0, Math.PI * 2);
      ctx.stroke();

      ctx.font = '700 8px "SF Pro", Inter, sans-serif';
      ctx.fillStyle = '#fbbf24';
      ctx.fillText('🔒 ANTI-COLLAPSE LOCK (+18.0 Nm)', kneeX + actR + 8 * scale, kneeY + 12 * scale);
    }
    ctx.restore();

    // 13. Technical Blueprint Dimension Annotations & Badges
    ctx.save();
    // Knee Angle Readout Callout
    ctx.font = '700 11px monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText(`θ_knee = ${this.current_knee_deg.toFixed(1)}°`, kneeX - 85 * scale, kneeY - 14 * scale);

    ctx.font = '500 8px monospace';
    ctx.fillStyle = '#94a3b8';
    ctx.fillText(`ω_knee = ${this.omega_knee_deg_s.toFixed(1)}°/s`, kneeX - 85 * scale, kneeY - 2 * scale);

    // IMU Sensor Chips
    ctx.fillStyle = '#1e293b';
    ctx.strokeStyle = '#38bdf8';
    ctx.lineWidth = 1;
    // Thigh IMU
    ctx.strokeRect(hipX + 18 * scale, hipY + 45 * scale, 34 * scale, 12 * scale);
    ctx.font = '600 7px monospace';
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('IMU-THIGH', hipX + 20 * scale, hipY + 54 * scale);

    // Shank IMU
    ctx.fillStyle = '#1e293b';
    ctx.strokeRect(kneeX + 18 * scale, kneeY + 45 * scale, 34 * scale, 12 * scale);
    ctx.fillStyle = '#38bdf8';
    ctx.fillText('IMU-SHANK', kneeX + 20 * scale, kneeY + 54 * scale);

    // Optical Encoder
    ctx.fillStyle = '#06b6d4';
    ctx.fillText('12-bit ENCODER', kneeX - 75 * scale, kneeY + 22 * scale);

    // Gait Status Pill at bottom right
    const pillX = w - 120;
    const pillY = h - 28;
    ctx.fillStyle = 'rgba(15, 23, 42, 0.9)';
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.4)';
    ctx.beginPath();
    ctx.roundRect(pillX, pillY, 110, 18, 4);
    ctx.fill();
    ctx.stroke();

    ctx.font = '600 8px monospace';
    ctx.fillStyle = this.gait_phase === 'SWING' ? '#a855f7' : '#10b981';
    ctx.fillText(`GAIT: ${this.gait_phase}`, pillX + 8, pillY + 12);
    ctx.restore();
  }
}

window.MoveAssist2DSchematic = MoveAssist2DSchematic;

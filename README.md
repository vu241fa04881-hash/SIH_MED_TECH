# MoveAssist: Standalone AI-Assisted Lower-Limb Rehabilitation Exoskeleton

**SIH 2026**: PS SIH26113  
**Team**: BERSERK TECHIES | **Team ID**: TEAM-147  
**Status**: Virtual Engineering Prototype & Proof-of-Concept  

> [!NOTE]
> **Scientific Disclaimer**: Virtual Engineering Prototype & Proof-of-Concept — Model estimates only, not direct biological measurements.

---

## 1. Executive Overview

**MoveAssist** is a standalone, closed-loop simulation and visual engineering application designed from the ground up to demonstrate adaptive **Assist-As-Needed (AAN)** lower-limb rehabilitation robotics.

The application pairs a **100 Hz scientific Python simulation engine** (handling Dempster/Winter anthropometrics, dynamic knee torque models with Butterworth filtering, virtual sensors, two-speed AAN control, and a multi-tier safety supervisor) with a high-fidelity **Three.js WebGL 3D digital twin** and **real-time HTML5 Canvas strip-charts** running in the browser.

---

## 2. Key System Capabilities

### 1. 3D Virtual Human & Articulated Exoskeleton Digital Twin
- Anatomically proportioned human model (torso, pelvis, thighs, knee hinges, shanks, ankles, and feet).
- Mechanical exoskeleton (carbon-fiber thigh cuff, lateral knee rotary BLDC actuator, telescopic aircraft-aluminum shank linkages, and articulated footplate bracket).
- **Dynamic Actuator Glow**: The lateral knee actuator halo shifts color in real time based on assistance torque intensity:
  - *Emerald Green*: Active user participation, low assistance ($\tau < 8\text{ Nm}$).
  - *Electric Cyan*: Balanced nominal assistance ($8 - 18\text{ Nm}$).
  - *Amber / Orange*: High assistance ($18 - 28\text{ Nm}$).
  - *Violet*: Active Protective Mode (spasm stabilization).
  - *Crimson Strobe*: Emergency Stop engaged.

### 2. Personalized Anthropometric Biomechanical Model
- Utilizes Dempster (1955) and Winter (2009) regression tables:
  - Thigh: $m_{thigh} = 0.1000 \cdot M$, $r_{COM} = 0.433 \cdot L_{thigh}$
  - Shank: $m_{shank} = 0.0465 \cdot M$, $r_{COM} = 0.433 \cdot L_{shank}$
  - Foot: $m_{foot} = 0.0145 \cdot M$, $r_{COM} = 0.500 \cdot L_{foot}$
- Moment of inertia computation about the knee joint axis:
  $$I_{knee,total} = I_{shank,knee} + I_{foot,knee}$$
- Interactive 4-step auto-calibration routine (`WEAR_DETECTED -> ZERO_SENSORS -> TARE_LOAD -> CALIBRATED`).

### 3. Biomechanical Knee Torque Model & Butterworth Filtering
- Theoretical single-joint knee torque estimation:
  $$\tau_{required} = \tau_{gravity} + \tau_{inertial} + \tau_{external}$$
- Where gravitational torque is:
  $$\tau_{gravity} = (m_{shank} r_{COM,shank} + m_{foot} L_{shank}) g \sin(\theta)$$
- To eliminate numerical differentiation spikes from $\dot{\theta}$ and $\ddot{\theta}$, numerical derivatives are processed through an online **2nd-order low-pass Butterworth filter** ($f_c = 6.0\text{ Hz}$ at $100\text{ Hz}$ sampling rate).

### 4. Virtual Sensor Suite
- **6-axis IMUs** on thigh and shank measuring angular rates, accelerations, and sagittal pitch with realistic Gaussian noise and drift.
- **Tri-zone FSR Foot Pressure Array** (Heel, Metatarsal, Toe) simulating biomechanical vertical ground reaction force (vGRF) and detecting stance vs. swing phases.
- **Optical Joint Encoder** with 12-bit quadrature resolution ($0.088^\circ$ step quantization).
- **Surface EMG (sEMG)** simulating rectus femoris neural drive envelope and spectral median frequency shift ($110\text{ Hz} \to 65\text{ Hz}$) tracking neuromuscular fatigue.

### 5. Two-Speed Adaptive Assist-As-Needed (AAN) Controller
- **Assistance Deficit**:
  $$\tau_{deficit} = \max(0, \tau_{required} - \tau_{user,estimated})$$
- **Fast Loop (100 Hz)**: Computes instantaneous torque commands, applies virtual impedance damping ($-B_{virtual} \dot{\theta}$), and passes to safety supervision.
- **Slow Loop (1-2 Hz)**: Multi-cycle performance monitoring:
  - $\text{User Contribution} \uparrow \implies \text{Assistance Gain } K_{AAN} \downarrow$ (encourages active recovery and neuroplasticity).
  - $\text{User Contribution} \downarrow \text{ or Fatigue} \uparrow \implies \text{Assistance Gain } K_{AAN} \uparrow$ (safeguards against gait collapse).

### 6. Safety Supervisor (Highest Authority)
- **Hard Torque Ceiling Clamping**: Strict limit of $\pm 35.0\text{ Nm}$.
- **Slew-Rate Limiter**: Clamped to $\le 120.0\text{ Nm/s}$ to prevent mechanical shock.
- **Anatomical ROM Limit**: Strictly enforced between $0.0^\circ$ and $115.0^\circ$ with soft pushback buffering.
- **Sensor Fault Detection**: Any signal loss or out-of-range anomaly triggers **Safe Fallback Mode**.
- **Latching Emergency Stop (E-Stop)**: Hardware-level instant cutoff to $0.0\text{ Nm}$.

### 7. Automated 5-Phase Clinical Demonstration Sequence
1. **Phase 1: Weak Patient** (User strength 20% $\implies$ High assistance ~85%)
2. **Phase 2: Patient Improvement** (User strength rises to 70% $\implies$ Assistance automatically drops to ~30%)
3. **Phase 3: Muscle Fatigue** (Fatigue accumulates $\implies$ Assistance steps in to support gait)
4. **Phase 4: Sudden Deterioration** (Spastic tremor injected $\implies$ Safety Supervisor activates Protective Mode with viscous dampening)
5. **Phase 5: Recovery** (Tremor clears $\implies$ Smooth return to normal adaptive AAN)

---

## 3. Project Architecture

```
ppp/
├── backend/
│   ├── __init__.py
│   ├── config.py              # System constants, anthropometrics, safety parameters
│   ├── server.py              # HTTP & SSE real-time streaming server (60 Hz)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── anthropometry.py   # Dempster/Winter tables & auto-calibration state machine
│   │   ├── biomechanics.py    # Dynamic knee torque model & Butterworth low-pass filter
│   │   └── user_model.py      # Estimated voluntary torque (tau_user_est) & fatigue model
│   ├── sensors/
│   │   ├── __init__.py
│   │   ├── imu.py             # 6-axis IMU with noise, drift & fault hooks
│   │   ├── foot_pressure.py   # Tri-zone FSR foot pressure sensor array & vGRF
│   │   ├── encoder.py         # Optical joint angle encoder with quantization
│   │   └── emg.py             # Surface EMG simulation & spectral fatigue shift
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── gait_fsm.py        # 6-stage clinical gait phase state machine
│   │   ├── deficit.py         # Assistance deficit calculator
│   │   ├── adaptive_aan.py    # Two-speed Assist-As-Needed adaptive controller
│   │   └── actuator.py        # Virtual BLDC motor with lag & saturation
│   ├── safety/
│   │   ├── __init__.py
│   │   └── supervisor.py      # Ceiling clamping, slew rate, ROM stops, E-Stop
│   └── simulation/
│       ├── __init__.py
│       ├── loop.py            # Master closed-loop simulation loop (100 Hz)
│       └── demo_runner.py     # 5-phase clinical demonstration engine
├── frontend/
│   ├── index.html             # Cockpit layout with SIH 2026 header & HUD
│   ├── css/
│   │   └── style.css          # Dark clinical theme, glassmorphism, responsive grid
│   └── js/
│       ├── vendor/            # Offline Three.js r128 & OrbitControls scripts
│       ├── three_app.js       # 3D Virtual Human + Articulated Exoskeleton + Sensors
│       ├── charts.js          # Multi-channel HTML5 Canvas strip charts
│       ├── dashboard.js       # Interactive controls, E-Stop, sliders & telemetry HUD
│       └── app.js             # Telemetry streaming client (SSE @ 60 Hz)
├── tests/
│   ├── __init__.py
│   ├── test_biomechanics.py   # Gravity/inertia verification & Butterworth filter tests
│   ├── test_safety.py         # Torque clamp, slew rate, ROM limits & E-Stop tests
│   ├── test_adaptive_aan.py   # AAN inverse adaptation verification
│   └── test_closed_loop.py    # End-to-end 100 Hz simulation cycle tests
├── run.py                     # Single-command launcher (starts server + opens browser)
└── README.md                  # Complete documentation
```

---

## 4. Quickstart & Verification

### Running Automated Tests
Run the complete unit and integration test suite:
```powershell
python -m unittest discover -s tests -v
```

### Starting the Application
Launch the simulation server and web cockpit with a single command:
```powershell
python run.py
```
This starts the 100 Hz simulation loop and opens your default browser at:
`http://127.0.0.1:8000`

---

## 5. Demonstration Guide

1. **Observe Baseline Gait**: In the 3D viewport, see the anatomical virtual human walking with the robotic exoskeleton. The knee actuator halo glows cyan/green.
2. **Start Demonstration**: Click `START DEMONSTRATION` on the right panel. Watch the 5-phase pipeline stepper:
   - *Phase 1*: High assistance torque delivered to the weak patient.
   - *Phase 2*: User strength rises; commanded assistance smoothly drops.
   - *Phase 3*: Muscle fatigue accumulates; assistance ramps up to prevent collapse.
   - *Phase 4*: Spastic tremors trigger Protective Mode with violet actuator glow and stabilizing damping.
   - *Phase 5*: Patient restabilizes, returning cleanly to adaptive AAN baseline.
3. **Test Safety Interlocks**:
   - Hit `EMERGENCY STOP` $\implies$ Actuator torque cuts to $0.0\text{ Nm}$ instantly, badge turns red, ring turns crimson. Click `Reset Latched E-Stop` to re-engage.
   - Click `IMU Dropout` or `FSR Disconnect` $\implies$ System immediately drops into `SAFE FALLBACK` mode. Click `Clear Faults` to restore.
4. **Tune Patient Anthropometrics**:
   - Modify Height and Mass inputs $\implies$ Segment masses, distal mass, and knee MOI recalculate instantaneously.
   - Click `Auto-Calibrate` to run the sensor taring sequence.

/**
 * MoveAssist 3D Virtual Human & Articulated Exoskeleton Digital Twin (Three.js)
 * SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
 */

class MoveAssist3DViewer {
  constructor(containerId) {
    this.container = document.getElementById(containerId);
    this.width = this.container.clientWidth || 800;
    this.height = this.container.clientHeight || 480;

    this.scene = null;
    this.camera = null;
    this.renderer = null;
    this.controls = null;

    // Model Components
    this.humanGroup = null;
    this.exoGroup = null;
    this.sensorGroup = null;

    // Articulated joint references
    this.pelvis = null;
    this.rightHip = null;
    this.rightThigh = null;
    this.rightKnee = null;
    this.rightShank = null;
    this.rightAnkle = null;
    this.rightFoot = null;

    this.leftHip = null;
    this.leftThigh = null;
    this.leftKnee = null;
    this.leftShank = null;

    // Exoskeleton moving parts
    this.actuatorCoreMesh = null;
    this.actuatorGlowLight = null;
    this.thighCuff = null;
    this.shankBrace = null;
    this.footPlate = null;

    // Sensor 3D visual markers
    this.fsrHeelMesh = null;
    this.fsrMetaMesh = null;
    this.fsrToeMesh = null;
    this.emgPatchMesh = null;
    this.thighImuMesh = null;
    this.shankImuMesh = null;

    // Layer visibility
    this.showExo = true;
    this.showAnatomy = true;
    this.showSensors = true;

    this.init();
  }

  init() {
    // 1. Scene Setup
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x090e18);
    this.scene.fog = new THREE.FogExp2(0x090e18, 0.08);

    // 2. Camera
    this.camera = new THREE.PerspectiveCamera(42, this.width / this.height, 0.1, 50.0);
    this.camera.position.set(2.4, 1.3, 2.8);

    // 3. Renderer
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: "high-performance" });
    this.renderer.setSize(this.width, this.height);
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.container.appendChild(this.renderer.domElement);

    // 4. Orbit Controls
    if (typeof THREE.OrbitControls !== 'undefined') {
      this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
      this.controls.enableDamping = true;
      this.controls.dampingFactor = 0.05;
      this.controls.target.set(0, 0.85, 0);
      this.controls.maxPolarAngle = Math.PI / 2 + 0.05;
      this.controls.minDistance = 1.0;
      this.controls.maxDistance = 6.0;
    }

    // 5. Lighting
    this.setupLighting();

    // 6. Environment & Floor Grid
    this.setupEnvironment();

    // 7. Build 3D Models
    this.buildVirtualHuman();
    this.buildExoskeleton();
    this.buildSensorMarkers();

    // Resize handling
    window.addEventListener('resize', () => this.onResize());

    // Render loop
    this.animate();
  }

  setupLighting() {
    const ambient = new THREE.AmbientLight(0x1e293b, 1.2);
    this.scene.add(ambient);

    const dirLight = new THREE.DirectionalLight(0xffffff, 1.4);
    dirLight.position.set(3, 5, 3);
    dirLight.castShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    this.scene.add(dirLight);

    const blueRim = new THREE.DirectionalLight(0x06b6d4, 0.9);
    blueRim.position.set(-3, 2, -2);
    this.scene.add(blueRim);

    const softFill = new THREE.PointLight(0x818cf8, 0.5, 8);
    softFill.position.set(0, 2, 2);
    this.scene.add(softFill);
  }

  setupEnvironment() {
    // Medical Gait Laboratory Floor Grid
    const grid = new THREE.GridHelper(10, 20, 0x06b6d4, 0x1e293b);
    grid.position.y = 0.0;
    this.scene.add(grid);

    // Subtle reflective ground disk
    const floorGeo = new THREE.CircleGeometry(4.5, 32);
    const floorMat = new THREE.MeshStandardMaterial({
      color: 0x0a0f1d,
      roughness: 0.6,
      metalness: 0.2
    });
    const floor = new THREE.Mesh(floorGeo, floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    this.scene.add(floor);
  }

  buildVirtualHuman() {
    this.humanGroup = new THREE.Group();
    this.humanGroup.name = "Human_Anatomy";

    const skinMat = new THREE.MeshStandardMaterial({
      color: 0x334155,
      roughness: 0.5,
      metalness: 0.15
    });

    const jointMat = new THREE.MeshStandardMaterial({
      color: 0x475569,
      roughness: 0.4,
      metalness: 0.3
    });

    // 1. Pelvis / Torso Base
    this.pelvis = new THREE.Group();
    this.pelvis.position.set(0, 0.95, 0);

    // Torso block
    const torsoGeo = new THREE.BoxGeometry(0.32, 0.45, 0.22);
    const torso = new THREE.Mesh(torsoGeo, skinMat);
    torso.position.y = 0.28;
    torso.castShadow = true;
    this.pelvis.add(torso);

    // Pelvis hip block
    const pelvisGeo = new THREE.CylinderGeometry(0.18, 0.16, 0.14, 16);
    const pelvisMesh = new THREE.Mesh(pelvisGeo, skinMat);
    pelvisMesh.rotation.z = Math.PI / 2;
    pelvisMesh.castShadow = true;
    this.pelvis.add(pelvisMesh);

    // 2. Right Leg (Instrumented Exoskeleton Side)
    this.rightHip = new THREE.Group();
    this.rightHip.position.set(0.12, -0.05, 0);

    // Thigh mesh
    const thighGeo = new THREE.CylinderGeometry(0.065, 0.052, 0.42, 16);
    const thighMesh = new THREE.Mesh(thighGeo, skinMat);
    thighMesh.position.y = -0.21;
    thighMesh.castShadow = true;

    this.rightThigh = new THREE.Group();
    this.rightThigh.add(thighMesh);
    this.rightHip.add(this.rightThigh);

    // Knee Joint Axis
    this.rightKnee = new THREE.Group();
    this.rightKnee.position.set(0, -0.42, 0);
    const kneeJointMesh = new THREE.Mesh(new THREE.SphereGeometry(0.045, 16, 16), jointMat);
    this.rightKnee.add(kneeJointMesh);
    this.rightThigh.add(this.rightKnee);

    // Shank mesh (Calf / Tibia)
    const shankGeo = new THREE.CylinderGeometry(0.05, 0.04, 0.42, 16);
    const shankMesh = new THREE.Mesh(shankGeo, skinMat);
    shankMesh.position.y = -0.21;
    shankMesh.castShadow = true;

    this.rightShank = new THREE.Group();
    this.rightShank.add(shankMesh);
    this.rightKnee.add(this.rightShank);

    // Ankle & Foot
    this.rightAnkle = new THREE.Group();
    this.rightAnkle.position.set(0, -0.42, 0);
    const ankleMesh = new THREE.Mesh(new THREE.SphereGeometry(0.035, 16, 16), jointMat);
    this.rightAnkle.add(ankleMesh);

    const footGeo = new THREE.BoxGeometry(0.08, 0.05, 0.22);
    const footMesh = new THREE.Mesh(footGeo, jointMat);
    footMesh.position.set(0, -0.025, 0.06);
    footMesh.castShadow = true;
    this.rightFoot = new THREE.Group();
    this.rightFoot.add(footMesh);
    this.rightAnkle.add(this.rightFoot);
    this.rightShank.add(this.rightAnkle);

    // 3. Left Leg (Contralateral reference leg)
    this.leftHip = new THREE.Group();
    this.leftHip.position.set(-0.12, -0.05, 0);
    this.leftThigh = new THREE.Group();
    const leftThighMesh = new THREE.Mesh(thighGeo, skinMat);
    leftThighMesh.position.y = -0.21;
    this.leftThigh.add(leftThighMesh);
    this.leftHip.add(this.leftThigh);

    this.leftKnee = new THREE.Group();
    this.leftKnee.position.set(0, -0.42, 0);
    this.leftShank = new THREE.Group();
    const leftShankMesh = new THREE.Mesh(shankGeo, skinMat);
    leftShankMesh.position.y = -0.21;
    this.leftShank.add(leftShankMesh);
    this.leftKnee.add(this.leftShank);
    this.leftThigh.add(this.leftKnee);

    const leftFoot = new THREE.Mesh(footGeo, jointMat);
    leftFoot.position.set(0, -0.44, 0.06);
    this.leftShank.add(leftFoot);

    this.pelvis.add(this.rightHip);
    this.pelvis.add(this.leftHip);
    this.humanGroup.add(this.pelvis);
    this.scene.add(this.humanGroup);
  }

  buildExoskeleton() {
    this.exoGroup = new THREE.Group();
    this.exoGroup.name = "Mechanical_Exoskeleton";

    // Carbon-fiber & Aircraft Titanium Materials
    const carbonMat = new THREE.MeshStandardMaterial({
      color: 0x111827,
      roughness: 0.3,
      metalness: 0.8
    });

    const titaniumMat = new THREE.MeshStandardMaterial({
      color: 0x94a3b8,
      roughness: 0.2,
      metalness: 0.95
    });

    // 1. Thigh Cuff (Mounted to rightThigh)
    this.thighCuff = new THREE.Group();
    const cuffGeo = new THREE.CylinderGeometry(0.078, 0.078, 0.16, 24, 1, true, -Math.PI * 0.7, Math.PI * 1.4);
    const cuffMesh = new THREE.Mesh(cuffGeo, carbonMat);
    cuffMesh.position.set(0, -0.20, 0);
    this.thighCuff.add(cuffMesh);

    // Lateral linkage down to knee actuator
    const thighLinkage = new THREE.Mesh(new THREE.BoxGeometry(0.02, 0.22, 0.03), titaniumMat);
    thighLinkage.position.set(0.082, -0.22, 0);
    this.thighCuff.add(thighLinkage);
    this.rightThigh.add(this.thighCuff);

    // 2. Rotary Knee Actuator (Mounted on lateral axis of rightKnee)
    const actuatorGroup = new THREE.Group();
    actuatorGroup.position.set(0.085, 0, 0);
    actuatorGroup.rotation.y = Math.PI / 2;

    // Outer Motor Housing Rim
    const rimGeo = new THREE.CylinderGeometry(0.055, 0.055, 0.025, 24);
    const rimMesh = new THREE.Mesh(rimGeo, titaniumMat);
    rimMesh.rotation.x = Math.PI / 2;
    actuatorGroup.add(rimMesh);

    // Dynamic Glowing Inner Core
    const coreGeo = new THREE.CylinderGeometry(0.038, 0.038, 0.027, 24);
    const coreMat = new THREE.MeshStandardMaterial({
      color: 0x06b6d4,
      emissive: 0x06b6d4,
      emissiveIntensity: 0.8,
      roughness: 0.2
    });
    this.actuatorCoreMesh = new THREE.Mesh(coreGeo, coreMat);
    this.actuatorCoreMesh.rotation.x = Math.PI / 2;
    actuatorGroup.add(this.actuatorCoreMesh);

    // Dynamic Point Light at actuator center
    this.actuatorGlowLight = new THREE.PointLight(0x06b6d4, 1.5, 1.2);
    actuatorGroup.add(this.actuatorGlowLight);

    // 3D Rotational Torque Direction Indicator Arc & Cone
    this.torqueIndicatorGroup = new THREE.Group();
    this.torqueIndicatorGroup.position.set(0, 0, 0.02);

    const arcGeo = new THREE.TorusGeometry(0.068, 0.0035, 8, 32, Math.PI * 0.7);
    this.torqueArcMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
    this.torqueArcMesh = new THREE.Mesh(arcGeo, this.torqueArcMat);
    this.torqueIndicatorGroup.add(this.torqueArcMesh);

    const coneGeo = new THREE.ConeGeometry(0.010, 0.022, 8);
    this.torqueConeMat = new THREE.MeshBasicMaterial({ color: 0x06b6d4 });
    this.torqueConeMesh = new THREE.Mesh(coneGeo, this.torqueConeMat);
    this.torqueConeMesh.position.set(0.068 * Math.cos(Math.PI * 0.7), 0.068 * Math.sin(Math.PI * 0.7), 0);
    this.torqueConeMesh.rotation.z = Math.PI * 0.7 + Math.PI / 2;
    this.torqueIndicatorGroup.add(this.torqueConeMesh);

    actuatorGroup.add(this.torqueIndicatorGroup);

    this.rightKnee.add(actuatorGroup);

    // 3. Shank Brace & Telescopic Linkage (Mounted on rightShank)
    this.shankBrace = new THREE.Group();
    const shankCuffGeo = new THREE.CylinderGeometry(0.065, 0.065, 0.14, 24, 1, true, -Math.PI * 0.7, Math.PI * 1.4);
    const shankCuffMesh = new THREE.Mesh(shankCuffGeo, carbonMat);
    shankCuffMesh.position.set(0, -0.22, 0);
    this.shankBrace.add(shankCuffMesh);

    const shankLinkage = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.24, 0.025), titaniumMat);
    shankLinkage.position.set(0.082, -0.18, 0);
    this.shankBrace.add(shankLinkage);
    this.rightShank.add(this.shankBrace);

    // 4. Articulated Footplate Orthosis (Mounted on rightFoot)
    this.footPlate = new THREE.Group();
    const plateGeo = new THREE.BoxGeometry(0.09, 0.015, 0.24);
    const plateMesh = new THREE.Mesh(plateGeo, carbonMat);
    plateMesh.position.set(0, -0.05, 0.06);
    this.footPlate.add(plateMesh);
    this.rightFoot.add(this.footPlate);

    this.scene.add(this.exoGroup);
  }

  buildSensorMarkers() {
    this.sensorGroup = new THREE.Group();
    this.sensorGroup.name = "Virtual_Sensors";

    // 1. Thigh 6-Axis IMU (Amber/Gold miniature housing)
    const imuGeo = new THREE.BoxGeometry(0.02, 0.012, 0.02);
    const imuMat = new THREE.MeshStandardMaterial({ color: 0xf59e0b, metalness: 0.8, roughness: 0.2 });
    this.thighImuMesh = new THREE.Mesh(imuGeo, imuMat);
    this.thighImuMesh.position.set(0, -0.15, 0.075);
    this.rightThigh.add(this.thighImuMesh);

    // 2. Shank 6-Axis IMU
    this.shankImuMesh = new THREE.Mesh(imuGeo, imuMat);
    this.shankImuMesh.position.set(0, -0.18, 0.06);
    this.rightShank.add(this.shankImuMesh);

    // 3. Rectus Femoris sEMG Electrode Patch (Glowing on anterior thigh)
    const emgGeo = new THREE.CylinderGeometry(0.018, 0.018, 0.005, 16);
    const emgMat = new THREE.MeshStandardMaterial({
      color: 0x10b981,
      emissive: 0x10b981,
      emissiveIntensity: 0.5,
      roughness: 0.3
    });
    this.emgPatchMesh = new THREE.Mesh(emgGeo, emgMat);
    this.emgPatchMesh.rotation.x = Math.PI / 2;
    this.emgPatchMesh.position.set(0, -0.10, 0.07);
    this.rightThigh.add(this.emgPatchMesh);

    // 4. Tri-Zone FSR Foot Pressure Discs (Heel, Metatarsal, Toe under foot sole)
    const fsrGeo = new THREE.CylinderGeometry(0.02, 0.02, 0.006, 16);
    const makeFsrMat = () => new THREE.MeshStandardMaterial({
      color: 0x06b6d4,
      emissive: 0x06b6d4,
      emissiveIntensity: 0.2,
      roughness: 0.4
    });

    this.fsrHeelMesh = new THREE.Mesh(fsrGeo, makeFsrMat());
    this.fsrHeelMesh.position.set(0, -0.055, -0.02);
    this.rightFoot.add(this.fsrHeelMesh);

    this.fsrMetaMesh = new THREE.Mesh(fsrGeo, makeFsrMat());
    this.fsrMetaMesh.position.set(0, -0.055, 0.07);
    this.rightFoot.add(this.fsrMetaMesh);

    this.fsrToeMesh = new THREE.Mesh(fsrGeo, makeFsrMat());
    this.fsrToeMesh.position.set(0, -0.055, 0.14);
    this.rightFoot.add(this.fsrToeMesh);

    this.scene.add(this.sensorGroup);
  }

  updateTelemetry(telemetry) {
    if (!telemetry || !telemetry.kinematics) return;

    const k = telemetry.kinematics;
    const kneeRad = THREE.MathUtils.degToRad(k.knee_angle_deg);
    const thighRad = THREE.MathUtils.degToRad(k.thigh_angle_deg);

    // 1. Mode-Aware Skeletal & Exoskeleton Articulation
    const km = (k.mode || "WALK").toUpperCase().replace("-", "_");

    if (km === "SIT_STAND") {
      // Bilateral synchronous movement with pelvic descent into chair
      const sitRatio = Math.min(1.0, Math.max(0.0, k.knee_angle_deg / 85.0));
      if (this.pelvis) {
        this.pelvis.position.y = 0.95 - (sitRatio * 0.38); // descent from 0.95m to 0.57m
        this.pelvis.position.z = -(sitRatio * 0.12);       // subtle posterior seating shift
      }
      if (this.rightHip) this.rightHip.rotation.x = -thighRad;
      if (this.rightKnee) this.rightKnee.rotation.x = kneeRad;
      if (this.leftHip) this.leftHip.rotation.x = -thighRad;
      if (this.leftKnee) this.leftKnee.rotation.x = kneeRad;
    } else if (km === "MANUAL_JOG") {
      if (this.pelvis) this.pelvis.position.set(0, 0.95, 0);
      if (this.rightHip) this.rightHip.rotation.x = -thighRad;
      if (this.rightKnee) this.rightKnee.rotation.x = kneeRad;
      if (this.leftHip) this.leftHip.rotation.x = 0;
      if (this.leftKnee) this.leftKnee.rotation.x = THREE.MathUtils.degToRad(10.0);
    } else if (km === "STANDBY") {
      if (this.pelvis) this.pelvis.position.set(0, 0.95, 0);
      if (this.rightHip) this.rightHip.rotation.x = 0;
      if (this.rightKnee) this.rightKnee.rotation.x = THREE.MathUtils.degToRad(10.0);
      if (this.leftHip) this.leftHip.rotation.x = 0;
      if (this.leftKnee) this.leftKnee.rotation.x = THREE.MathUtils.degToRad(10.0);
    } else {
      // WALK and RUN: Reciprocal gait kinematics
      if (this.pelvis) this.pelvis.position.set(0, 0.95, 0);
      if (this.rightHip) this.rightHip.rotation.x = -thighRad;
      if (this.rightKnee) this.rightKnee.rotation.x = kneeRad;
      if (this.leftHip) this.leftHip.rotation.x = thighRad * 0.9;
      if (this.leftKnee) {
        const leftKneeDeg = (k.knee_angle_deg > 30.0) ? (60.0 - k.knee_angle_deg) : (k.knee_angle_deg * 0.4);
        this.leftKnee.rotation.x = THREE.MathUtils.degToRad(leftKneeDeg);
      }
    }

    // 2. Actuator Dynamic Glow & Halo Color Shift
    const torque = Math.abs(telemetry.torques?.commanded_nm || 0);
    const mode = telemetry.safety?.mode || "NORMAL_AAN";

    let glowColor = 0x06b6d4;      // Cyan (Nominal)
    let intensity = 0.4 + (torque / 35.0) * 1.6;

    if (mode === "EMERGENCY_STOP") {
      glowColor = 0xf43f5e;       // Crimson strobe
      intensity = (Date.now() % 400 < 200) ? 2.5 : 0.2;
    } else if (mode === "PROTECTIVE_MODE") {
      glowColor = 0x8b5cf6;       // Violet (Protective)
      intensity = 1.8;
    } else if (mode === "CONTROLLED_SOFT_STOP") {
      glowColor = 0xf59e0b;       // Amber Gold (Controlled Anti-Fall Soft Stop)
      intensity = 1.5 + 0.6 * Math.sin(Date.now() * 0.008); // Gentle glowing pulse
    } else if (mode === "SAFE_FALLBACK") {
      glowColor = 0xf59e0b;       // Amber (Fallback)
      intensity = 1.2;
    } else {
      // Color gradient from Emerald (low assist) -> Cyan -> Amber -> Rose
      if (torque < 8.0) {
        glowColor = 0x10b981;     // Emerald (active patient, low assist)
      } else if (torque < 18.0) {
        glowColor = 0x06b6d4;     // Cyan (moderate assist)
      } else if (torque < 28.0) {
        glowColor = 0xf59e0b;     // Amber (high assist)
      } else {
        glowColor = 0xf43f5e;     // Rose (near limit)
      }
    }

    if (this.actuatorCoreMesh) {
      this.actuatorCoreMesh.material.color.setHex(glowColor);
      this.actuatorCoreMesh.material.emissive.setHex(glowColor);
      this.actuatorCoreMesh.material.emissiveIntensity = intensity;
    }
    if (this.actuatorGlowLight) {
      this.actuatorGlowLight.color.setHex(glowColor);
      this.actuatorGlowLight.intensity = intensity * 1.5;
    }

    // Dynamic 3D Rotational Torque Direction Indicator update
    if (this.torqueIndicatorGroup) {
      const rawCmdTorque = telemetry.torques?.commanded_nm ?? 0.0;
      const absTorque = Math.abs(rawCmdTorque);
      if (absTorque < 0.3 || mode === "EMERGENCY_STOP") {
        this.torqueIndicatorGroup.visible = false;
      } else {
        this.torqueIndicatorGroup.visible = true;
        const isExtension = rawCmdTorque >= 0;
        const indColor = mode === "CONTROLLED_SOFT_STOP" ? 0xfbbf24 : (isExtension ? 0x10b981 : 0xa855f7);
        if (this.torqueArcMat) this.torqueArcMat.color.setHex(indColor);
        if (this.torqueConeMat) this.torqueConeMat.color.setHex(indColor);
        // Flip rotation for extension (positive) vs flexion (negative)
        this.torqueIndicatorGroup.rotation.z = isExtension ? 0 : Math.PI;
        const scaleVal = Math.min(1.35, 0.85 + (absTorque / 35.0) * 0.5);
        this.torqueIndicatorGroup.scale.set(scaleVal, scaleVal, scaleVal);
      }
    }

    // 3. FSR Pressure Discs Scaling & Brightness
    const fsr = telemetry.sensors?.foot_pressure;
    if (fsr && this.fsrHeelMesh) {
      const hScale = 1.0 + Math.min(1.5, (fsr.heel_n || 0) / 300.0);
      this.fsrHeelMesh.scale.set(hScale, 1.0, hScale);
      this.fsrHeelMesh.material.emissiveIntensity = Math.min(2.0, (fsr.heel_n || 0) / 200.0);

      const mScale = 1.0 + Math.min(1.5, (fsr.metatarsal_n || 0) / 300.0);
      this.fsrMetaMesh.scale.set(mScale, 1.0, mScale);
      this.fsrMetaMesh.material.emissiveIntensity = Math.min(2.0, (fsr.metatarsal_n || 0) / 200.0);

      const tScale = 1.0 + Math.min(1.5, (fsr.toe_n || 0) / 300.0);
      this.fsrToeMesh.scale.set(tScale, 1.0, tScale);
      this.fsrToeMesh.material.emissiveIntensity = Math.min(2.0, (fsr.toe_n || 0) / 200.0);
    }

    // 4. EMG Patch Electrical Activation Glow
    const emgEnv = telemetry.sensors?.emg?.envelope_norm || 0;
    if (this.emgPatchMesh) {
      this.emgPatchMesh.material.emissiveIntensity = 0.3 + (emgEnv * 1.8);
    }
  }

  toggleLayer(layerName, visible) {
    if (layerName === 'exo' && this.thighCuff && this.shankBrace && this.footPlate) {
      this.showExo = visible;
      this.thighCuff.visible = visible;
      this.shankBrace.visible = visible;
      this.footPlate.visible = visible;
      if (this.actuatorCoreMesh) this.actuatorCoreMesh.parent.visible = visible;
    } else if (layerName === 'anatomy' && this.humanGroup) {
      this.showAnatomy = visible;
      this.humanGroup.visible = visible;
    } else if (layerName === 'sensors') {
      this.showSensors = visible;
      if (this.thighImuMesh) this.thighImuMesh.visible = visible;
      if (this.shankImuMesh) this.shankImuMesh.visible = visible;
      if (this.emgPatchMesh) this.emgPatchMesh.visible = visible;
      if (this.fsrHeelMesh) {
        this.fsrHeelMesh.visible = visible;
        this.fsrMetaMesh.visible = visible;
        this.fsrToeMesh.visible = visible;
      }
    }
  }

  resetCamera() {
    if (this.camera && this.controls) {
      this.camera.position.set(2.4, 1.3, 2.8);
      this.controls.target.set(0, 0.85, 0);
      this.controls.update();
    }
  }

  onResize() {
    if (!this.container || !this.renderer || !this.camera) return;
    this.width = this.container.clientWidth;
    this.height = this.container.clientHeight;
    this.camera.aspect = this.width / this.height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(this.width, this.height);
  }

  animate() {
    requestAnimationFrame(() => this.animate());
    if (this.controls) this.controls.update();
    if (this.renderer && this.scene && this.camera) {
      this.renderer.render(this.scene, this.camera);
    }
  }
}

window.MoveAssist3DViewer = MoveAssist3DViewer;

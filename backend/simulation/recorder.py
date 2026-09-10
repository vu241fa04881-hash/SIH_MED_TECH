"""Trial Telemetry Data Recorder
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import threading
from typing import List, Dict, Any, Optional


class TrialRecorder:
    """Records high-resolution simulation frames during 5-phase clinical demonstrations

    or continuous rehabilitation sessions for export into Microsoft Excel (.xlsx).
    """

    def __init__(self, max_records: int = 15000):
        self.max_records = max_records
        self.lock = threading.Lock()
        self.is_recording = False
        self.demo_trial_records: List[Dict[str, Any]] = []
        self.rolling_buffer: List[Dict[str, Any]] = []

    def start_recording(self) -> None:
        with self.lock:
            self.demo_trial_records.clear()
            self.is_recording = True

    def stop_recording(self) -> None:
        with self.lock:
            self.is_recording = False

    def record_step(self, telemetry: Dict[str, Any]) -> None:
        """Captures and flattens a complete simulation telemetry frame."""
        k = telemetry.get("kinematics", {})
        t = telemetry.get("torques", {})
        aan = telemetry.get("aan", {})
        gait = telemetry.get("gait", {})
        sensors = telemetry.get("sensors", {})
        safety = telemetry.get("safety", {})
        actuator = telemetry.get("actuator", {})
        demo = telemetry.get("demo", {})

        imu_thigh = sensors.get("imu_thigh", {})
        imu_shank = sensors.get("imu_shank", {})
        encoder = sensors.get("encoder", {})
        fsr = sensors.get("foot_pressure", {})
        emg = sensors.get("emg", {})

        flattened = {
            "timestamp_s": telemetry.get("timestamp_s", 0.0),
            "step": telemetry.get("step", 0),
            
            # Demonstration Phase
            "demo_phase_num": demo.get("phase", 0),
            "demo_phase_name": demo.get("name", "MANUAL_MODE"),
            
            # Gait Phase
            "gait_phase": gait.get("phase", "INITIAL_CONTACT"),
            "gait_cycle_pct": gait.get("cycle_percent", 0.0),
            "stride_count": gait.get("stride_count", 0),
            
            # Kinematics & Joint Angles
            "kinematic_mode": k.get("mode", "WALK"),
            "knee_angle_deg": k.get("knee_angle_deg", 0.0),
            "thigh_angle_deg": k.get("thigh_angle_deg", 0.0),
            "shank_angle_deg": k.get("shank_angle_deg", 0.0),
            "knee_vel_deg_s": k.get("knee_velocity_deg_s", 0.0),
            
            # Torques & Power
            "tau_req_nm": t.get("required_nm", 0.0),
            "tau_grav_nm": t.get("gravity_nm", 0.0),
            "tau_inert_nm": t.get("inertial_nm", 0.0),
            "tau_ext_nm": t.get("external_nm", 0.0),
            "tau_user_nm": t.get("user_estimated_nm", 0.0),
            "tau_deficit_nm": t.get("deficit_nm", 0.0),
            "tau_cmd_nm": t.get("commanded_nm", 0.0),
            "tau_act_nm": t.get("actuator_output_nm", 0.0),
            "mech_power_w": telemetry.get("power", {}).get("mechanical_watts", 0.0),
            "elec_power_w": telemetry.get("power", {}).get("electrical_watts", 0.0),
            "human_strength_used_pct": telemetry.get("power", {}).get("human_strength_used_pct", 50.0),
            "exo_strength_used_pct": telemetry.get("power", {}).get("exo_strength_used_pct", 50.0),
            
            # AAN & Patient Parameters
            "k_aan": aan.get("k_aan", 0.70),
            "assistance_pct": aan.get("assistance_percent", 50.0),
            "user_pct": aan.get("user_percent", 50.0),
            "user_strength": aan.get("user_strength", 0.35),
            "fatigue_index": aan.get("fatigue_index", 0.0),
            
            # Virtual Sensors - IMUs
            "imu_thigh_pitch_deg": imu_thigh.get("pitch_deg", 0.0),
            "imu_thigh_gyro_deg_s": imu_thigh.get("gyro_z_deg_s", 0.0),
            "imu_thigh_accel_x": imu_thigh.get("accel_x_g", 0.0),
            "imu_thigh_accel_y": imu_thigh.get("accel_y_g", 0.0),
            "imu_shank_pitch_deg": imu_shank.get("pitch_deg", 0.0),
            "imu_shank_gyro_deg_s": imu_shank.get("gyro_z_deg_s", 0.0),
            "imu_shank_accel_x": imu_shank.get("accel_x_g", 0.0),
            "imu_shank_accel_y": imu_shank.get("accel_y_g", 0.0),
            
            # Virtual Sensors - Encoder
            "encoder_angle_deg": encoder.get("angle_deg", 0.0),
            "encoder_vel_deg_s": encoder.get("velocity_deg_s", 0.0),
            "encoder_counts": encoder.get("raw_counts", 0),
            
            # Virtual Sensors - Tri-Zone FSR
            "fsr_heel_n": fsr.get("heel_n", 0.0),
            "fsr_meta_n": fsr.get("metatarsal_n", 0.0),
            "fsr_toe_n": fsr.get("toe_n", 0.0),
            "fsr_total_grf_n": fsr.get("total_grf_n", 0.0),
            "fsr_is_stance": "STANCE" if fsr.get("is_stance", False) else "SWING",
            
            # Virtual Sensors - sEMG
            "emg_envelope": emg.get("envelope_norm", 0.0),
            "emg_raw_uV": emg.get("raw_uV", 0.0),
            "emg_median_freq_hz": emg.get("median_freq_hz", 110.0),
            
            # Safety & Diagnostics
            "safety_mode": safety.get("mode", "NORMAL_AAN"),
            "e_stop_latched": safety.get("e_stop_latched", False),
            "motor_temp_c": actuator.get("motor_temp_c", 32.0),
            "alerts_str": "; ".join(safety.get("alerts", [])) if safety.get("alerts") else "NONE"
        }

        with self.lock:
            # Maintain rolling buffer
            self.rolling_buffer.append(flattened)
            if len(self.rolling_buffer) > 3000:
                self.rolling_buffer.pop(0)

            # Record demo trial
            if self.is_recording:
                self.demo_trial_records.append(flattened)
                if len(self.demo_trial_records) >= self.max_records:
                    self.is_recording = False

    def get_records_for_report(self) -> List[Dict[str, Any]]:
        with self.lock:
            if len(self.demo_trial_records) > 10:
                return list(self.demo_trial_records)
            return list(self.rolling_buffer)

    def get_status(self) -> Dict[str, Any]:
        with self.lock:
            return {
                "is_recording": self.is_recording,
                "recorded_samples": len(self.demo_trial_records),
                "has_trial_data": len(self.demo_trial_records) > 0,
                "rolling_samples": len(self.rolling_buffer)
            }

import bpy
import math
import os

# Clean active scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Create Skeleton Rig (Armature)
bpy.ops.object.armature_add(enter_editmode=True, align='WORLD', location=(0, 0, 0))
arm_obj = bpy.context.active_object
arm_obj.name = "Human_Exo_Rig"
eb = arm_obj.data.edit_bones

# Pelvis / Root
root = eb['Bone']
root.name = 'Hips'
root.head = (0, 0, 1.0)
root.tail = (0, 0, 1.1)

# Lower Limb Chains
for side, x in [('L', -0.18), ('R', 0.18)]:
    # Femur / Thigh with subtle anatomical pre-flexion bend (-Y is anterior in Blender)
    up_leg = eb.new(f'UpLeg_{side}')
    up_leg.head = (x, 0.0, 1.0)
    up_leg.tail = (x, -0.018, 0.52)
    up_leg.parent = root

    # Tibia / Shank
    leg = eb.new(f'Leg_{side}')
    leg.head = (x, -0.018, 0.52)
    leg.tail = (x, 0.0, 0.08)
    leg.parent = up_leg
    leg.use_connect = True

    # Foot / Ankle
    foot = eb.new(f'Foot_{side}')
    foot.head = (x, 0.0, 0.08)
    foot.tail = (x, -0.22, 0.0)
    foot.parent = leg
    foot.use_connect = True

    # Inverse Kinematics (IK) Foot Target Controller
    foot_ik = eb.new(f'Foot_IK_{side}')
    foot_ik.head = (x, 0.0, 0.08)
    foot_ik.tail = (x, -0.22, 0.08)
    foot_ik.parent = None  # Independent kinematic target

    # Knee Pole Target (Positioned anteriorly in front of the knee to guide natural posterior flexion)
    knee_pole = eb.new(f'Knee_Pole_{side}')
    knee_pole.head = (x, -0.65, 0.52)
    knee_pole.tail = (x, -0.75, 0.52)
    knee_pole.parent = None  # Independent pole vector controller

# Switch to POSE mode to apply IK and Strict Biomechanical Range of Motion (ROM) Constraints
bpy.ops.object.mode_set(mode='POSE')
for side in ['L', 'R']:
    pose_leg = arm_obj.pose.bones[f'Leg_{side}']
    
    # 1. 2-Bone Inverse Kinematics Solver Constraint
    ik_con = pose_leg.constraints.new('IK')
    ik_con.name = f'IK_Limb_{side}'
    ik_con.target = arm_obj
    ik_con.subtarget = f'Foot_IK_{side}'
    ik_con.chain_count = 2
    ik_con.pole_target = arm_obj
    ik_con.pole_subtarget = f'Knee_Pole_{side}'
    # Adjusted pole vector so knee flexes posteriorly (backward) and steps anteriorly (forward) with proper foot placement
    ik_con.pole_angle = math.radians(-90.0)

    # 2. Strict Anatomical Joint Limits (ROM: 0° to 120° Flexion, Zero Hyperextension / Recurvatum)
    rom_limit = pose_leg.constraints.new('LIMIT_ROTATION')
    rom_limit.name = f'Knee_ROM_Limit_{side}'
    rom_limit.owner_space = 'LOCAL'
    rom_limit.use_limit_x = True
    rom_limit.min_x = 0.0                   # 0° Strict Extension Limit (prevents hyperextension / recurvatum)
    rom_limit.max_x = math.radians(120.0)   # 120° Physiological Flexion Limit

bpy.ops.object.mode_set(mode='OBJECT')

# Shaders / Materials
mat_human = bpy.data.materials.new(name="Human_Anatomy_Mat")
mat_human.use_nodes = True
mat_human.node_tree.nodes["Principled BSDF"].inputs['Base Color'].default_value = (0.15, 0.22, 0.32, 1.0)

mat_metal = bpy.data.materials.new(name="Exo_Metal_Mat")
mat_metal.use_nodes = True
bsdf_metal = mat_metal.node_tree.nodes["Principled BSDF"]
bsdf_metal.inputs['Base Color'].default_value = (0.05, 0.06, 0.08, 1.0)
bsdf_metal.inputs['Metallic'].default_value = 0.95
bsdf_metal.inputs['Roughness'].default_value = 0.25

mat_led = bpy.data.materials.new(name="Exo_Cyan_Glow")
mat_led.use_nodes = True
bsdf_led = mat_led.node_tree.nodes["Principled BSDF"]
bsdf_led.inputs['Base Color'].default_value = (0.0, 0.85, 1.0, 1.0)
if "Emission Color" in bsdf_led.inputs:
    bsdf_led.inputs['Emission Color'].default_value = (0.0, 0.85, 1.0, 1.0)
    bsdf_led.inputs['Emission Strength'].default_value = 4.0
elif "Emission" in bsdf_led.inputs:
    bsdf_led.inputs['Emission'].default_value = (0.0, 0.85, 1.0, 1.0)

# Geometry Helper
def create_component(name, bone_name, prim_type, pos, scale, mat, rot=(0, 0, 0)):
    if prim_type == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=1.0, location=pos, rotation=rot)
    elif prim_type == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(radius=1.0, depth=1.0, location=pos, rotation=rot)
    elif prim_type == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=0.045, minor_radius=0.008, location=pos, rotation=rot)

    obj = bpy.context.active_object
    obj.name = name
    if prim_type != 'torus':
        obj.scale = scale
    obj.data.materials.append(mat)
    obj.parent = arm_obj
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    return obj

# Human anatomy proxies
create_component("Human_Pelvis", "Hips", 'cube', (0, 0, 1.0), (0.42, 0.22, 0.16), mat_human)
for s, x in [('L', -0.18), ('R', 0.18)]:
    create_component(f"Human_Thigh_{s}", f"UpLeg_{s}", 'cylinder', (x, 0, 0.76), (0.08, 0.08, 0.48), mat_human)
    create_component(f"Human_Shank_{s}", f"Leg_{s}", 'cylinder', (x, 0, 0.30), (0.065, 0.065, 0.44), mat_human)

# Exoskeleton hardware elements
for s, x in [('L', -0.18), ('R', 0.18)]:
    x_off = x * 1.35
    create_component(f"Exo_PelvisMount_{s}", "Hips", 'cylinder', (x * 1.3, 0, 0.98), (0.12, 0.12, 0.06), mat_metal)
    create_component(f"Exo_FemurStrut_{s}", f"UpLeg_{s}", 'cylinder', (x_off, 0, 0.74), (0.022, 0.022, 0.38), mat_metal)
    create_component(f"Exo_ActuatorKnee_{s}", f"UpLeg_{s}", 'cylinder', (x_off, 0, 0.52), (0.055, 0.055, 0.05), mat_metal, (0, math.radians(90), 0))
    create_component(f"Exo_LEDIndicator_{s}", f"UpLeg_{s}", 'torus', (x_off + (0.03 if x > 0 else -0.03), 0, 0.52), (1, 1, 1), mat_led, (0, math.radians(90), 0))
    create_component(f"Exo_TibiaStrut_{s}", f"Leg_{s}", 'cylinder', (x_off, 0, 0.30), (0.02, 0.02, 0.36), mat_metal)
    create_component(f"Exo_CalfCuff_{s}", f"Leg_{s}", 'cylinder', (x, 0, 0.32), (0.09, 0.09, 0.04), mat_metal)

# Export assets
out_dir = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(out_dir, exist_ok=True)

blend_path = os.path.join(out_dir, "exo_human_rigged.blend")
glb_path = os.path.join(out_dir, "exo_digital_twin.glb")

bpy.ops.wm.save_as_mainfile(filepath=blend_path)
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    use_selection=False,
    export_yup=True,
    export_skins=True,
    export_morph=True
)
print(f"[SUCCESS] Exported rigged blend to: {blend_path}")
print(f"[SUCCESS] Exported digital twin GLB to: {glb_path}")

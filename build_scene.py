# build_scene.py — "The Lighthouse at the Edge of the World"
# Blender 4.2 headless scene builder + renderer (Eevee Next).
# Run:  MODE=stills|full  FRAMES=528  blender -b --python build_scene.py
#   stills -> renders frames 1 / 164 / 264 / 528 as PNGs into ./stills/
#   full   -> renders the whole PNG sequence into ./frames/
# No living beings. No music (voiceover muxed later by ffmpeg).
import bpy
import math
import os
import random

MODE = os.environ.get("MODE", "stills")
FRAMES = int(os.environ.get("FRAMES", "528"))  # 22s @ 24fps; ffmpeg -shortest trims to voice
FPS = 24
W, H = 1280, 720

random.seed(7)

# ---------------------------------------------------------------- clean
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for coll in (bpy.data.meshes, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
    pass  # data blocks are freed with objects; leftovers harmless

# ---------------------------------------------------------------- helpers
def mat_principled(name, color, roughness=0.7, metallic=0.0,
                   emission=None, emission_strength=0.0, alpha=1.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    if emission is not None:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission_strength
    if alpha < 1.0:
        bsdf.inputs["Alpha"].default_value = alpha
        m.blend_method = "BLEND"
    return m

def add_mesh(obj, mat):
    if mat:
        obj.data.materials.append(mat)
    return obj

def key_rot(obj, frame, z):
    obj.rotation_euler = (0.0, 0.0, z)
    obj.keyframe_insert(data_path="rotation_euler", frame=frame)

# ---------------------------------------------------------------- render settings
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE_NEXT"
scene.render.resolution_x = W
scene.render.resolution_y = H
scene.render.resolution_percentage = 100
scene.render.fps = FPS
scene.frame_start = 1
scene.frame_end = FRAMES
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Base Contrast"  # 4.2 enum: no plain "Medium Contrast"
ee = scene.eevee
ee.taa_render_samples = 32
if hasattr(ee, "use_bloom"):
    ee.use_bloom = True
    ee.bloom_threshold = 0.7
if hasattr(ee, "use_gtao"):
    ee.use_gtao = True
if hasattr(ee, "use_soft_shadows"):
    ee.use_soft_shadows = True

# ---------------------------------------------------------------- world: dusk sky
world = bpy.data.worlds["World"]
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]
sky = nt.nodes.new("ShaderNodeTexSky")
sky.sky_type = "NISHITA"
sky.sun_elevation = 0.06          # sun just above horizon -> dusk (v1 0.03 = hard black band)
sky.sun_rotation = 0.6
sky.altitude = 0.2
sky.air_density = 1.6
sky.dust_density = 2.2
sky.ozone_density = 1.0
nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
bg.inputs["Strength"].default_value = 0.7

# ---------------------------------------------------------------- materials
MAT_ROCK   = mat_principled("MAT_Rock",   (0.16, 0.13, 0.11), roughness=0.95)
MAT_WHITE  = mat_principled("MAT_TowerWhite", (0.92, 0.90, 0.85), roughness=0.65)
MAT_RED    = mat_principled("MAT_BandRed", (0.55, 0.08, 0.06), roughness=0.6)
MAT_DARK   = mat_principled("MAT_Dark",   (0.12, 0.12, 0.13), roughness=0.8)
MAT_ROOF   = mat_principled("MAT_Roof",   (0.28, 0.05, 0.05), roughness=0.6)
MAT_LAMP   = mat_principled("MAT_Lamp",   (0.05, 0.03, 0.01), roughness=0.3,
                            emission=(1.0, 0.75, 0.35), emission_strength=6.0)
MAT_MOON   = mat_principled("MAT_Moon",   (0.9, 0.9, 0.85), roughness=0.4,
                            emission=(0.9, 0.9, 0.85), emission_strength=0.9)
MAT_STAR   = mat_principled("MAT_Star",   (1.0, 1.0, 1.0), roughness=0.2,
                            emission=(1.0, 1.0, 1.0), emission_strength=2.5)
MAT_CLOUD  = mat_principled("MAT_Cloud",  (0.75, 0.70, 0.75), roughness=1.0, alpha=0.45)

# ocean: dark blue, animated noise bump via #frame driver on mapping
MAT_OCEAN = mat_principled("MAT_Ocean", (0.015, 0.07, 0.15), roughness=0.22, metallic=0.15)
ont = MAT_OCEAN.node_tree
obsdf = ont.nodes["Principled BSDF"]
omap = ont.nodes.new("ShaderNodeMapping")
otex = ont.nodes.new("ShaderNodeTexNoise")
otex.inputs["Scale"].default_value = 6.0
otex.inputs["Detail"].default_value = 3.0
obump = ont.nodes.new("ShaderNodeBump")
obump.inputs["Strength"].default_value = 0.2  # v1 0.35 read as a tan/blue checkerboard
otexcoord = ont.nodes.new("ShaderNodeTexCoord")
ont.links.new(otexcoord.outputs["Generated"], omap.inputs["Vector"])
ont.links.new(omap.outputs["Vector"], otex.inputs["Vector"])
ont.links.new(otex.outputs["Fac"], obump.inputs["Height"])
ont.links.new(obump.outputs["Normal"], obsdf.inputs["Normal"])
drv = omap.inputs["Location"].driver_add("default_value", 0)
drv.driver.expression = "frame * 0.002"
drv2 = omap.inputs["Location"].driver_add("default_value", 1)
drv2.driver.expression = "frame * 0.001"

# beam: mostly transparent, warm emissive (narrower + fainter than v1 —
# v1 read as a giant solid white wedge in the sky)
MAT_BEAM = bpy.data.materials.new("MAT_Beam")
MAT_BEAM.use_nodes = True
bnt = MAT_BEAM.node_tree
bem = bnt.nodes.new("ShaderNodeEmission")
bem.inputs["Color"].default_value = (1.0, 0.82, 0.45, 1.0)
bem.inputs["Strength"].default_value = 1.2
btr = bnt.nodes.new("ShaderNodeBsdfTransparent")
bmix = bnt.nodes.new("ShaderNodeMixShader")
bmix.inputs[0].default_value = 0.92  # mostly transparent
bout = bnt.nodes["Material Output"]
bnt.links.new(btr.outputs["BSDF"], bmix.inputs[1])
bnt.links.new(bem.outputs["Emission"], bmix.inputs[2])
bnt.links.new(bmix.outputs["Shader"], bout.inputs["Surface"])
MAT_BEAM.blend_method = "BLEND"

# ---------------------------------------------------------------- ocean
bpy.ops.mesh.primitive_grid_add(x_subdivisions=64, y_subdivisions=64, size=220,
                                location=(0, 0, 0))
ocean = bpy.context.active_object
ocean.name = "Ocean"
add_mesh(ocean, MAT_OCEAN)
wave = ocean.modifiers.new("Waves", "WAVE")
wave.height = 0.35
wave.width = 2.0
wave.speed = 0.8
wave.lifetime = 0.0
# NOTE: WaveModifier has no 'damping' in Blender 4.2 — removed

# ---------------------------------------------------------------- island rock
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=(0, 0, 0.4))
island = bpy.context.active_object
island.name = "Island"
island.scale = (7.0, 6.0, 2.4)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
tex_rock = bpy.data.textures.new("RockClouds", "CLOUDS")
tex_rock.noise_scale = 2.5
disp = island.modifiers.new("RockDisplace", "DISPLACE")
disp.texture = tex_rock
disp.strength = 1.1
add_mesh(island, MAT_ROCK)

# scattered rocks in the water
for i, (x, y, s) in enumerate([(-9, 4, 1.6), (8, -6, 1.2), (10, 5, 0.9),
                               (-6, -8, 1.4), (3, 9, 0.8), (-11, -3, 1.0)]):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0, location=(x, y, -0.1))
    rock = bpy.context.active_object
    rock.name = f"Rock_{i}"
    rock.scale = (s, s * 0.8, s * 0.55)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    d = rock.modifiers.new("Displace", "DISPLACE")
    d.texture = tex_rock
    d.strength = 0.5
    add_mesh(rock, MAT_ROCK)

# ---------------------------------------------------------------- lighthouse
def cyl(name, r_top, r_bot, depth, z, mat, verts=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r_top, depth=depth,
                                        location=(0, 0, z))
    o = bpy.context.active_object
    o.name = name
    o.scale = (1.0, 1.0, 1.0)
    # taper: bottom radius via second cylinder trick — use scale on lower ring is complex;
    # keep straight cylinders with different radii per segment (stylised look)
    add_mesh(o, mat)
    return o

base_z = 2.4  # island top ~ z 2.4 at centre
cyl("TowerBase", 1.55, 1.55, 1.0, base_z + 0.5, MAT_DARK)
cyl("TowerSeg1", 1.45, 1.45, 2.2, base_z + 2.1, MAT_WHITE)
cyl("TowerBand1", 1.48, 1.48, 0.9, base_z + 3.65, MAT_RED)
cyl("TowerSeg2", 1.30, 1.30, 2.2, base_z + 5.2, MAT_WHITE)
cyl("TowerBand2", 1.33, 1.33, 0.9, base_z + 6.75, MAT_RED)
cyl("TowerSeg3", 1.15, 1.15, 1.6, base_z + 8.0, MAT_WHITE)
cyl("Gallery", 1.55, 1.55, 0.3, base_z + 9.0, MAT_DARK)
# railing torus
bpy.ops.mesh.primitive_torus_add(major_radius=1.5, minor_radius=0.05,
                                 major_segments=32, minor_segments=8,
                                 location=(0, 0, base_z + 9.35))
rail = bpy.context.active_object
rail.name = "Railing"
add_mesh(rail, MAT_DARK)
# lamp room (glowing)
cyl("LampRoom", 0.95, 0.95, 1.3, base_z + 9.8, MAT_LAMP, verts=24)
# roof cone
bpy.ops.mesh.primitive_cone_add(radius1=1.15, radius2=0.05, depth=1.0,
                                location=(0, 0, base_z + 10.95))
roof = bpy.context.active_object
roof.name = "Roof"
add_mesh(roof, MAT_ROOF)
# finial
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.12, location=(0, 0, base_z + 11.55))
fin = bpy.context.active_object
fin.name = "Finial"
add_mesh(fin, MAT_DARK)

LAMP_Z = base_z + 9.8

# ---------------------------------------------------------------- rotating beam rig
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, LAMP_Z))
beam_rig = bpy.context.active_object
beam_rig.name = "BeamRig"
for sign, label in ((1, "A"), (-1, "B")):
    bpy.ops.mesh.primitive_cone_add(radius1=0.25, radius2=1.1, depth=25.0,
                                    location=(sign * 12.5, 0, 0))
    cone = bpy.context.active_object
    cone.name = f"Beam_{label}"
    cone.rotation_euler = (0, math.radians(90 if sign > 0 else -90), 0)
    add_mesh(cone, MAT_BEAM)
    cone.parent = beam_rig
    # spotlight along the same direction
    spot = bpy.data.lights.new(f"Spot_{label}", type="SPOT")
    spot.energy = 500.0
    spot.color = (1.0, 0.8, 0.45)
    spot.spot_size = math.radians(14)
    spot.spot_blend = 0.4
    spot_obj = bpy.data.objects.new(f"Spot_{label}", spot)
    bpy.context.collection.objects.link(spot_obj)
    spot_obj.location = (sign * 0.5, 0, 0)
    spot_obj.rotation_euler = (0, math.radians(-90 if sign > 0 else 90), 0)
    spot_obj.parent = beam_rig
# beam rotates one full turn across the video, starting 90 deg off the
# camera axis — v2 frame 1 had a beam pointing straight down the lens
# (camera sat inside the 40-unit cone: full-frame whiteout). With a
# 25-unit beam the camera stays outside the cone, so the one mid-video
# pass-by is a soft flash, not a whiteout.
key_rot(beam_rig, 1, math.radians(90))
key_rot(beam_rig, FRAMES, math.radians(90 + 360))

# lamp point light
pl = bpy.data.lights.new("LampPoint", type="POINT")
pl.energy = 120.0
pl.color = (1.0, 0.75, 0.4)
pl_obj = bpy.data.objects.new("LampPoint", pl)
bpy.context.collection.objects.link(pl_obj)
pl_obj.location = (0, 0, LAMP_Z)

# ---------------------------------------------------------------- sun (dusk, low, warm)
sun = bpy.data.lights.new("Sun", type="SUN")
sun.energy = 2.0
sun.color = (1.0, 0.55, 0.25)
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (math.radians(78), 0, math.radians(35))

# ---------------------------------------------------------------- moon
bpy.ops.mesh.primitive_uv_sphere_add(radius=3.0, segments=32, ring_count=16,
                                     location=(55, -70, 55))
moon = bpy.context.active_object
moon.name = "Moon"
add_mesh(moon, MAT_MOON)

# ---------------------------------------------------------------- stars (dome of tiny emissive dots)
for i in range(90):
    a = random.uniform(0, 2 * math.pi)
    e = random.uniform(0.15, 1.2)
    r = 130.0
    x = r * math.cos(e) * math.cos(a)
    y = r * math.cos(e) * math.sin(a)
    z = r * math.sin(e) + 5
    s = random.uniform(0.08, 0.22)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=s, segments=6, ring_count=4,
                                         location=(x, y, z))
    st = bpy.context.active_object
    st.name = f"Star_{i}"
    add_mesh(st, MAT_STAR)

# ---------------------------------------------------------------- clouds (soft flattened blobs)
for i, (x, y, z, sx, sy, sz) in enumerate([
        (-45, -40, 34, 14, 6, 3.5), (30, -55, 40, 18, 8, 4),
        (55, 25, 36, 12, 6, 3), (-20, 55, 42, 16, 7, 3.5)]):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, segments=16, ring_count=12,
                                         location=(x, y, z))
    cl = bpy.context.active_object
    cl.name = f"Cloud_{i}"
    cl.scale = (sx, sy, sz)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_mesh(cl, MAT_CLOUD)

# ---------------------------------------------------------------- camera orbit rig
# v1 framing cut the lamp room + roof off the top of every frame:
# pull back, raise camera and aim point so the WHOLE tower fits
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 6.5))
cam_target = bpy.context.active_object
cam_target.name = "CamTarget"
bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0, 0, 6.5))
cam_rig = bpy.context.active_object
cam_rig.name = "CamRig"
cam_data = bpy.data.cameras.new("CAM_Main")
cam_data.lens = 35
cam = bpy.data.objects.new("CAM_Main", cam_data)
bpy.context.collection.objects.link(cam)
cam.parent = cam_rig
cam.location = (36.0, 0.0, 8.0)
trk = cam.constraints.new("TRACK_TO")
trk.target = cam_target
trk.track_axis = "TRACK_NEGATIVE_Z"
trk.up_axis = "UP_Y"
scene.camera = cam
# slow orbit: ~70 degrees across the video
key_rot(cam_rig, 1, 0.0)
key_rot(cam_rig, FRAMES, math.radians(70))

# ---------------------------------------------------------------- render
out_dir = os.path.join(os.getcwd(), "stills" if MODE == "stills" else "frames")
os.makedirs(out_dir, exist_ok=True)
if MODE == "stills":
    for f in (1, 164, FRAMES // 2, FRAMES):  # 164 = beam/camera crossing frame
        scene.frame_current = f
        scene.render.filepath = os.path.join(out_dir, f"still_{f:04d}.png")
        bpy.ops.render.render(write_still=True)
        print(f"STILL done frame {f}")
else:
    scene.render.filepath = os.path.join(out_dir, "frame_")
    bpy.ops.render.render(animation=True)
    print(f"FULL render done: {FRAMES} frames -> {out_dir}")
print("BUILD_SCENE_OK", MODE, FRAMES)

"""Build a low-poly medieval arming sword (one-handed) with Blender's Python API.

Run:  python3 sword/build_sword.py          (needs `pip install bpy==4.2.0`)

Outputs go to sword/export/ (.blend, .fbx, .obj, .glb) and sword/renders/ (.png).
The sword stands along +Z with the origin where the blade meets the guard,
so the grip hangs below the origin. Units are meters (~0.95 m long overall).
"""
import math
import os

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
EXPORT_DIR = os.path.join(HERE, "export")
RENDER_DIR = os.path.join(HERE, "renders")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_material(name, color, metallic, roughness):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    mat.diffuse_color = (*color, 1.0)  # viewport / some importers
    return mat


def mesh_object(name, bm, material):
    mesh = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(mesh)
    bm.free()
    for poly in mesh.polygons:
        poly.use_smooth = False  # flat shading for the low-poly look
    mesh.materials.append(material)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return obj


def loft(bm, rings, cap_start=True, cap_end=True):
    """Connect a list of equal-length vertex rings with quads."""
    for a, b in zip(rings, rings[1:]):
        n = len(a)
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if cap_start:
        bm.faces.new(list(reversed(rings[0])))
    if cap_end:
        bm.faces.new(rings[-1])


def build_blade(mat):
    """Diamond cross-section blade that tapers to a point."""
    bm = bmesh.new()
    # (height, half width, half thickness)
    sections = [
        (0.000, 0.027, 0.0070),
        (0.040, 0.026, 0.0068),
        (0.450, 0.022, 0.0060),
        (0.650, 0.015, 0.0050),
        (0.730, 0.006, 0.0030),
    ]
    rings = []
    for z, hw, ht in sections:
        rings.append([
            bm.verts.new((hw, 0, z)),
            bm.verts.new((0, ht, z)),
            bm.verts.new((-hw, 0, z)),
            bm.verts.new((0, -ht, z)),
        ])
    loft(bm, rings, cap_start=True, cap_end=False)
    tip = bm.verts.new((0, 0, 0.775))
    last = rings[-1]
    for i in range(4):
        bm.faces.new((last[i], last[(i + 1) % 4], tip))
    return mesh_object("Blade", bm, mat)


def build_guard(mat):
    """Straight cross-guard whose quillons narrow and tilt slightly toward the blade."""
    bm = bmesh.new()
    # (x, half depth y, half height z, z offset)
    sections = [
        (-0.105, 0.009, 0.008, 0.010),
        (-0.085, 0.011, 0.010, 0.004),
        (-0.025, 0.014, 0.013, 0.000),
        (0.025, 0.014, 0.013, 0.000),
        (0.085, 0.011, 0.010, 0.004),
        (0.105, 0.009, 0.008, 0.010),
    ]
    rings = []
    for x, hy, hz, dz in sections:
        rings.append([
            bm.verts.new((x, -hy, -hz + dz)),
            bm.verts.new((x, hy, -hz + dz)),
            bm.verts.new((x, hy, hz + dz)),
            bm.verts.new((x, -hy, hz + dz)),
        ])
    loft(bm, rings)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object("Guard", bm, mat)
    obj.location.z = -0.013
    return obj


def build_grip(mat):
    """Octagonal, slightly barrel-shaped grip."""
    bm = bmesh.new()
    sides = 8
    # (z, radius)
    sections = [(-0.026, 0.015), (-0.075, 0.018), (-0.124, 0.015)]
    rings = []
    for z, r in sections:
        ring = []
        for i in range(sides):
            a = 2 * math.pi * i / sides + math.pi / sides
            ring.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        rings.append(ring)
    loft(bm, rings)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_object("Grip", bm, mat)


def build_pommel(mat):
    """Wheel pommel (disc facing sideways) with a small peen on the end."""
    bm = bmesh.new()
    bmesh.ops.create_cone(
        bm, cap_ends=True, segments=8, radius1=0.032, radius2=0.032, depth=0.024,
    )
    # Stand the disc on edge so it faces sideways like a wheel.
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0),
                     matrix=Matrix.Rotation(math.pi / 2, 3, "X"))
    peen = bmesh.new()
    bmesh.ops.create_cone(
        peen, cap_ends=True, segments=6, radius1=0.008, radius2=0.006, depth=0.012,
    )
    bmesh.ops.translate(peen, verts=peen.verts, vec=(0, 0, -0.036))
    tmp = bpy.data.meshes.new("tmp")
    peen.to_mesh(tmp)
    peen.free()
    bm.from_mesh(tmp)
    bpy.data.meshes.remove(tmp)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    obj = mesh_object("Pommel", bm, mat)
    obj.location.z = -0.150
    return obj


def build_sword():
    steel = make_material("Steel", (0.78, 0.80, 0.83), 1.0, 0.30)
    iron = make_material("DarkIron", (0.22, 0.22, 0.24), 1.0, 0.45)
    leather = make_material("Leather", (0.16, 0.07, 0.03), 0.0, 0.65)

    parts = [
        build_blade(steel),
        build_guard(iron),
        build_grip(leather),
        build_pommel(iron),
    ]
    root = bpy.data.objects.new("MedievalSword", None)
    bpy.context.collection.objects.link(root)
    for p in parts:
        p.parent = root
    return root, parts


def setup_render():
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = True
    scene.render.film_transparent = False

    world = bpy.data.worlds.new("World")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.82, 0.84, 0.88, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    scene.world = world

    key = bpy.data.lights.new("Key", "AREA")
    key.energy = 120
    key.size = 1.0
    key_obj = bpy.data.objects.new("Key", key)
    key_obj.location = (0.9, -1.0, 1.2)
    key_obj.rotation_euler = (math.radians(50), 0, math.radians(40))
    scene.collection.objects.link(key_obj)

    rim = bpy.data.lights.new("Rim", "AREA")
    rim.energy = 60
    rim.size = 0.6
    rim_obj = bpy.data.objects.new("Rim", rim)
    rim_obj.location = (-0.8, 0.9, 0.6)
    rim_obj.rotation_euler = (math.radians(-60), 0, math.radians(-140))
    scene.collection.objects.link(rim_obj)

    cam = bpy.data.cameras.new("Camera")
    cam.type = "ORTHO"
    cam_obj = bpy.data.objects.new("Camera", cam)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    return scene, cam_obj


def aim(cam_obj, location, target):
    cam_obj.location = location
    direction = Vector(target) - Vector(location)
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def render(scene, path, res):
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def main():
    reset_scene()
    root, parts = build_sword()
    os.makedirs(EXPORT_DIR, exist_ok=True)
    os.makedirs(RENDER_DIR, exist_ok=True)

    tris = sum(len(p.data.polygons) for p in parts)
    print(f"faces: {tris}")

    # Exports (before cameras/lights are added, so files hold only the sword).
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(EXPORT_DIR, "medieval_sword.blend"))
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(EXPORT_DIR, "medieval_sword.fbx"),
        object_types={"MESH", "EMPTY"},
        apply_scale_options="FBX_SCALE_UNITS",
        mesh_smooth_type="FACE",
    )
    bpy.ops.wm.obj_export(filepath=os.path.join(EXPORT_DIR, "medieval_sword.obj"))
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(EXPORT_DIR, "medieval_sword.glb"), export_format="GLB",
    )

    scene, cam = setup_render()
    # Full view: sword leaned diagonally across a portrait frame.
    root.rotation_euler = (0, math.radians(-35), 0)
    aim(cam, (-0.17, -2.0, 0.25), (-0.17, 0, 0.25))
    cam.data.ortho_scale = 0.95
    render(scene, os.path.join(RENDER_DIR, "sword_full.png"), (1280, 1280))

    # Hilt close-up, three-quarter view.
    root.rotation_euler = (0, 0, 0)
    aim(cam, (0.55, -0.75, 0.15), (0, 0, -0.06))
    cam.data.ortho_scale = 0.38
    render(scene, os.path.join(RENDER_DIR, "sword_hilt.png"), (1080, 1080))


if __name__ == "__main__":
    main()

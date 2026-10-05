"""Characters on the real Roblox R15 body mesh (reference/roblox_r15.obj, exported from
Roblox Studio), with clothing painted like Roblox Shirt/Pants and baked onto the
mesh's own R15 UV layout.

How the painting reaches Roblox's UVs:
  1. Paint a "template" canvas: one cell per body part, front/back/left/right/top/bottom
     (style2.Painter - easy to draw in, like a clothing template).
  2. Give every body part a second UV map ("Paint") that projects each face of the mesh
     onto its side of that template.
  3. Cycles bakes template -> the original Roblox UV map, so the result is a normal
     R15 texture.

Run:  python3 cyclops/r15_real.py  -> export/r15/<Name>.fbx + <Name>_texture.png, renders/r15_<Name>.png
"""
import math
import os
import sys

import bpy  # must come first: it makes bmesh/mathutils importable
import bmesh
from mathutils import Matrix, Vector
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import style2  # noqa: E402

REFERENCE = os.path.join(HERE, "reference", "roblox_r15.obj")
OUT = os.path.join(HERE, "export", "r15")
RENDERS = os.path.join(HERE, "renders")


# ---------------------------------------------------------------------------
def load_reference():
    """Import the Studio-exported rig, face it toward -Y with feet on z = 0, and name
    every part by its R15 name. Returns {part: object} with origins at part centers."""
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=REFERENCE, use_split_groups=True)
    objs = [o for o in bpy.data.objects if o.type == "MESH" and o not in before]
    # The OBJ's front faces +Y after import; turn it around so front is -Y.
    allv = [o.matrix_world @ v.co for o in objs for v in o.data.vertices]
    lo = Vector([min(getattr(v, a) for v in allv) for a in "xyz"])
    hi = Vector([max(getattr(v, a) for v in allv) for a in "xyz"])
    centre = Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    to_origin = Matrix.Rotation(math.pi, 4, "Z") @ Matrix.Translation(-centre)
    parts = {}
    for o in objs:
        o.data.transform(to_origin @ o.matrix_world)
        o.matrix_world = Matrix.Identity(4)
        vs = [v.co for v in o.data.vertices]
        c = Vector([(min(getattr(v, a) for v in vs) + max(getattr(v, a) for v in vs)) / 2 for a in "xyz"])
        size = Vector([max(getattr(v, a) for v in vs) - min(getattr(v, a) for v in vs) for a in "xyz"])
        o.data.transform(Matrix.Translation(-c))
        o.location = c
        parts[identify(c, size)] = o
    for name, o in parts.items():
        o.name = o.data.name = name
        o.data.uv_layers.active.name = "UVMap"
    assert len(parts) == 15, sorted(parts)
    strip_face_features(parts["Head"])
    return parts


def strip_face_features(head):
    """The Studio head carries the classic Roblox eyes and smile as small raised meshes
    on its front. Cyclopes have one painted eye and no mouth, so remove those islands."""
    bm = bmesh.new()
    bm.from_mesh(head.data)
    seen, doomed = set(), []
    for v in bm.verts:
        if v in seen:
            continue
        island, stack = [], [v]
        seen.add(v)
        while stack:
            x = stack.pop()
            island.append(x)
            for e in x.link_edges:
                o = e.other_vert(x)
                if o not in seen:
                    seen.add(o)
                    stack.append(o)
        dims = [max(getattr(q.co, a) for q in island) - min(getattr(q.co, a) for q in island) for a in "xyz"]
        cy = sum(q.co.y for q in island) / len(island)
        if max(dims) < 0.5 and cy < -0.4:  # small and on the face (front is -Y)
            doomed += island
    bmesh.ops.delete(bm, geom=doomed, context="VERTS")
    bm.to_mesh(head.data)
    bm.free()


def identify(c, size):
    side = "Left" if c.x > 0.25 else "Right" if c.x < -0.25 else ""
    if not side:
        if size.x < 1.5:
            return "Head"
        return "UpperTorso" if size.z > 1.0 else "LowerTorso"
    arm = abs(c.x) > 1.0
    if size.z < 0.5:
        return side + ("Hand" if arm else "Foot")
    # Upper/lower by height within the limb.
    if arm:
        return side + ("UpperArm" if c.z > 3.05 else "LowerArm")
    return side + ("UpperLeg" if c.z > 1.2 else "LowerLeg")


def add_paint_uv(obj, part):
    """Second UV map projecting each face onto its side of the template canvas."""
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    uv = bm.loops.layers.uv.new("Paint")
    xs = [v.co.x for v in bm.verts]
    ys = [v.co.y for v in bm.verts]
    zs = [v.co.z for v in bm.verts]
    lo, hi = Vector((min(xs), min(ys), min(zs))), Vector((max(xs), max(ys), max(zs)))
    span = hi - lo
    bm.normal_update()
    for f in bm.faces:
        side = style2.dominant_face(f.normal)
        x0, y0, x1, y1 = style2.face_rect(part, side)
        for loop in f.loops:
            p = loop.vert.co - lo
            nx, ny, nz = p.x / span.x, p.y / span.y, p.z / span.z
            u, v = {
                "front": (nx, 1 - nz), "back": (1 - nx, 1 - nz),
                "left": (ny, 1 - nz), "right": (1 - ny, 1 - nz),
                "top": (nx, ny), "bottom": (nx, 1 - ny),
            }[side]
            loop[uv].uv = ((x0 + u * (x1 - x0)) / style2.CANVAS, 1 - (y0 + v * (y1 - y0)) / style2.CANVAS)
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.uv_layers.active = obj.data.uv_layers["UVMap"]
    obj.data.uv_layers["UVMap"].active_render = True


def bake(parts, template_path, out_path, size=1024):
    """Bake the template (via the Paint UVs) into Roblox's own UV layout."""
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 4
    scene.render.bake.margin = 6
    template = bpy.data.images.load(template_path)
    target = bpy.data.images.new("Baked", size, size)
    mat = bpy.data.materials.new("BakeMat")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    emit = nt.nodes.new("ShaderNodeEmission")
    uvn = nt.nodes.new("ShaderNodeUVMap")
    uvn.uv_map = "Paint"
    src = nt.nodes.new("ShaderNodeTexImage")
    src.image = template
    dst = nt.nodes.new("ShaderNodeTexImage")
    dst.image = target
    nt.links.new(uvn.outputs["UV"], src.inputs["Vector"])
    nt.links.new(src.outputs["Color"], emit.inputs["Color"])
    nt.links.new(emit.outputs["Emission"], out.inputs["Surface"])
    nt.nodes.active = dst
    bpy.ops.object.select_all(action="DESELECT")
    for o in parts.values():
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.select_set(True)
    bpy.context.view_layer.objects.active = next(iter(parts.values()))
    bpy.ops.object.bake(type="EMIT")
    target.filepath_raw = out_path
    target.file_format = "PNG"
    target.save()
    return target


def final_material(img, name):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    t = mat.node_tree.nodes.new("ShaderNodeTexImage")
    t.image = img
    mat.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.8
    return mat


def export(objs, path):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, object_types={"MESH"},
                             path_mode="COPY", embed_textures=True, axis_forward="Z", axis_up="Y")


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.preferences.filepaths.save_version = 0
    os.makedirs(OUT, exist_ok=True)
    name, painter, _spec, _extras = style2.villager()
    template = painter.save(os.path.join(OUT, f"{name}_template.png"))
    parts = load_reference()
    for part, o in parts.items():
        add_paint_uv(o, part)
    img = bake(parts, template, os.path.join(OUT, f"{name}_texture.png"))
    mat = final_material(img, name)
    for part, o in parts.items():
        o.data.materials.clear()
        o.data.materials.append(mat)
        o.name = o.data.name = f"{part}_Body"
    export(list(parts.values()), os.path.join(OUT, f"{name}.fbx"))
    style2.render(list(parts.values()), "R15" + name)


if __name__ == "__main__":
    main()

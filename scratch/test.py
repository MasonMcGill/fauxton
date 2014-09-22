from os.path import realpath, splitext
from bpy import data, ops

################################################################################
################################################################################

materials = {}

def get_material(source):
    if source is None:
        return None
    if source in materials:
        return materials[source]

    script_text = data.texts.new('')
    script_text.write(source)
    material = data.materials.new('')
    material.use_nodes = True

    nodes = material.node_tree.nodes
    nodes.clear()
    script = nodes.new('ShaderNodeScript')
    emittor = nodes.new('ShaderNodeEmission')
    output = nodes.new('ShaderNodeOutputMaterial')
    script.script = script_text

    links = material.node_tree.links
    links.new(script.outputs[0], emittor.inputs[0])
    links.new(emittor.outputs[0], output.inputs[0])

    materials[source] = material
    return material

################################################################################
################################################################################

def use_scene(path):
    materials.clear()
    ops.wm.open_mainfile(filepath=realpath(path))

class Camera:
    def __init__(self, source=None):
        self.resolution = (256, 256)
        self.field_of_view = (0.8, 0.8)
        self.position = (0, 0, 0)
        self.velocity = (0, 0, 0)
        self.rotation = (0, 0, 0)
        self.angular_velocity = (0, 0, 0)
        self.source = source
        self._material = get_material(source)

    def render(self, path):
        if self._material is not None:
            old_materials = {}
            for obj in data.objects:
                if hasattr(obj.data, 'materials'):
                    old_materials[obj.name] = list(obj.data.materials)
                    obj.data.materials.clear()
                    obj.data.materials.append(self._material)

        ext = splitext(path)[1][1:].lower()
        file_format = {'jpg': 'JPEG', 'png': 'PNG', 'exr': 'OPEN_EXR'}[ext]
        scene = data.scenes[0]
        scene.render.filepath = path
        scene.render.image_settings.file_format = file_format
        scene.render.resolution_x = 2 * self.resolution[0]
        scene.render.resolution_y = 2 * self.resolution[1]
        scene.camera.data.angle_x = self.field_of_view[0]
        scene.camera.data.angle_x = self.field_of_view[0]
        ops.render.render(write_still=True)

        if self._material is not None:
            for obj in data.objects:
                if obj.name in old_materials:
                    obj.data.materials.clear()
                    for material in old_materials[obj.name]:
                        obj.data.materials.append(material)

class DepthCamera(Camera):
    def __init__(self):
        super().__init__('''
            #include "stdosl.h"
            shader depth(output color result = color(0)) {
              point position_rt_camera = transform("camera", P);
              result = color(position_rt_camera[2]);
            }''')

class SurfaceNormalCamera(Camera):
    def __init__(self):
        super().__init__('''
            #include "stdosl.h"
            shader surface_normal(output color result = color(0)) {
              normal normal_rt_camera = transform("camera", N);
              result = color(normal_rt_camera);
            }''')

class VelocityCamera(Camera):
    def __init__(self):
        super().__init__('''
            #include "stdosl.h"
            shader optical_flow(output color result = color(0)) {
              vector velocity_rt_camera = transform("camera", dPdtime);
              result = color(velocity_rt_camera);
            }''')

class CompoundCamera:
    def __init__(self, components):
        self.components = components

    def render(self, path):
        base_path, ext = splitext(path)
        for view_name, component in self.components.items():
            component.render(base_path + view_name + ext)

class StereoCamera(CompoundCamera):
    ...

class ReflectivityCamera(Camera):
    def __init__(self):
        ...

################################################################################
################################################################################

use_scene('test.blend')
Camera().render('image.exr')
DepthCamera().render('depth.exr')
SurfaceNormalCamera().render('surface_normal.exr')
VelocityCamera().render('velocity.exr')

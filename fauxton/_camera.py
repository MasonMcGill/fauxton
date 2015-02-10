from os.path import dirname
from shutil import rmtree

try: from cv2 import IMREAD_UNCHANGED, imread
except ImportError: imread = None

from numpy import (array, arccos, arctan2, cos, cross, dot, hstack, load, pi,
                   sin, square, sqrt)

from _core import BlenderModule
from _scene import Prop

__name__ = 'fauxton'
__all__ = ['Camera', 'DepthSensor', 'SurfaceNormalSensor', 'VelocitySensor']

#===============================================================================
# Private Symbols
#===============================================================================

bl_camera = BlenderModule('''
    from contextlib import contextmanager
    from os.path import join
    from tempfile import mkdtemp
    from numpy import array, reshape, save

    DEFAULT_RESOLUTION = (256, 256)

    materials = {}

    def create_material(source):
        script_text = bpy.data.texts.new('')
        script_text.write(source)
        material = bpy.data.materials.new('')
        material.use_nodes = True

        nodes = material.node_tree.nodes
        nodes.clear()
        script = nodes.new('ShaderNodeScript')
        emittor = nodes.new('ShaderNodeEmission')
        output = nodes.new('ShaderNodeOutputMaterial')
        bpy.context.scene.render.engine = 'CYCLES'
        script.script = script_text

        if len(script.outputs) == 0:
            raise ValueError('A camera\\'s OSL shader must '
                             'provide at least 1 output.')

        links = material.node_tree.links
        links.new(script.outputs[0], emittor.inputs[0])
        links.new(emittor.outputs[0], output.inputs[0])

        material.use_fake_user = True
        return material

    def get_material_name(source):
        if not source in materials:
            materials[source] = create_material(source)
        return materials[source].name

    @contextmanager
    def use_material(scene, material_name):
        if material_name is not None:
            old_horizon_color = scene.world.horizon_color
            scene.render.engine = 'CYCLES'
            scene.world.horizon_color = (0, 0, 0)
            new_material = bpy.data.materials[material_name]
            old_materials = {}
            for obj in scene.objects:
                if hasattr(obj.data, 'materials'):
                    old_materials[obj.name] = list(obj.data.materials)
                    obj.data.materials.clear()
                    obj.data.materials.append(new_material)
        yield
        if material_name is not None:
            scene.world.horizon_color = old_horizon_color
            for obj in scene.objects:
                if hasattr(obj.data, 'materials'):
                    obj.data.materials.clear()
                    for material in old_materials[obj.name]:
                        obj.data.materials.append(material)

    def save_links(links):
        src = lambda l: (l.from_node, l.from_socket.name)
        snk = lambda l: (l.to_node, l.to_socket.name)
        return [src(l) + snk(l) for l in links]

    def load_links(links, link_info):
        for src_n, src_s, snk_n, snk_s in link_info:
            src = src_n.outputs[src_s]
            snk = snk_n.inputs[snk_s]
            links.new(src, snk)

    @contextmanager
    def use_render_pass(scene, render_pass_name):
        if render_pass_name is not None:
            scene_use_nodes = scene.use_nodes
            scene.use_nodes = True
            nodes = scene.node_tree.nodes
            links = scene.node_tree.links
            layer = scene.render.layers[0]
            passes = [a for a in dir(layer) if a.startswith('use_pass_')]
            scene_enabled_passes = [p for p in passes if getattr(layer, p)]
            scene_node_links = save_links(links)
            for p in passes: setattr(layer, p, False)
            setattr(layer, 'use_pass_' + render_pass_name, True)
            links.clear()
            is_composite = lambda n: n.bl_idname == 'CompositorNodeComposite'
            src_node = nodes.new('CompositorNodeRLayers')
            snk_node = next(filter(is_composite, nodes), None)
            snk_node = snk_node or nodes.new('CompositorNodeComposite')
            src_socket = next(s for s in src_node.outputs if s.enabled)
            snk_socket = snk_node.inputs['Image']
            links.new(src_socket, snk_socket)
        yield
        if render_pass_name is not None:
            nodes.remove(src_node)
            setattr(layer, 'use_pass_' + render_pass_name, False)
            for p in scene_enabled_passes: setattr(layer, p, True)
            load_links(links, scene_node_links)
            scene.use_nodes = scene_use_nodes

    @contextmanager
    def use_render_engine(scene, render_engine_name):
        if render_engine_name is not None:
            scene_render_engine = scene.render.engine
            scene.render.engine = render_engine_name
        yield
        if render_engine_name is not None:
            scene.render.engine = scene_render_engine

    def create(type_):
        camera = bpy.data.objects.new('', bpy.data.cameras.new(''))
        camera['__type__'] = type_
        return camera

    def get_field_of_view(camera):
        return [camera.data.angle_y, camera.data.angle_x]

    def set_field_of_view(camera, field_of_view):
        camera.data.angle_y, camera.data.angle_x = field_of_view

    def get_resolution(camera):
        return camera.get('resolution', DEFAULT_RESOLUTION)

    def set_resolution(camera, resolution):
        camera['resolution'] = resolution

    def get_source(camera):
        return camera.get('source', None)

    def set_source(camera, source):
        if 'source' in camera:
            del camera['source']
            del camera['material_name']
        if source is not None:
            camera['source'] = source
            camera['material_name'] = get_material_name(source)

    def get_render_pass(camera):
        return camera.get('render_pass', None)

    def set_render_pass(camera, render_pass):
        camera['render_pass'] = render_pass

    def get_render_engine(camera):
        return camera.get('render_engine', None)

    def set_render_engine(camera, render_engine):
        camera['render_engine'] = render_engine

    def render(camera, format):
        try: path = join(mkdtemp(dir='/dev/shm'), 'image.exr')
        except: path = join(mkdtemp(), 'image.exr')

        scene = camera.users_scene[0]
        scene.camera = camera
        scene.render.filepath = path
        scene.render.image_settings.file_format = 'OPEN_EXR'
        scene.render.resolution_y = 2 * get_resolution(camera)[0]
        scene.render.resolution_x = 2 * get_resolution(camera)[1]
        bpy.context.screen.scene = scene

        with use_render_engine(scene, get_render_engine(camera)):
            with use_render_pass(scene, get_render_pass(camera)):
                with use_material(scene, camera.get('material_name', None)):
                    bpy.ops.render.render(write_still=True)

        if format == 'exr':
            return path
        else:
            image = bpy.data.images.load(path)
            shape = (image.size[0], image.size[1], 4)
            save(path[:-3] + 'npy', reshape(array(image.pixels[:], 'f'), shape))
            image.user_clear(); bpy.data.images.remove(image)
            return path[:-3] + 'npy'
  ''')

#===============================================================================
# Public Symbols
#===============================================================================

class Camera(Prop):
    '''
    A prop that can take snapshots of its surroundings.

    :param dict \**properties: Initial values of instance variables.

    :var numpy.ndarray field_of_view: *y* and *x* viewing angles, in radians.
    :var numpy.ndarray resolution: *y* and *x* resolution, in pixels.
    :var str source: OSL source to use as an emissive material when rendering.
    :var str render_pass: Blender render pass to use (e.g. "z" or "color").
    :var str render_engine: Blender render engine to use (e.g. "CYCLES").
    '''
    resource_type = 'CAMERA'

    def __new__(cls, **properties):
        result = bl_camera.create(cls.resource_type)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    @property
    def field_of_view(self):
        return array(bl_camera.get_field_of_view(self))

    @field_of_view.setter
    def field_of_view(self, field_of_view):
        bl_camera.set_field_of_view(self, list(map(float, field_of_view)))

    @property
    def resolution(self):
        return array(bl_camera.get_resolution(self))

    @resolution.setter
    def resolution(self, resolution):
        bl_camera.set_resolution(self, list(map(float, resolution)))

    @property
    def source(self):
        return bl_camera.get_source(self)

    @source.setter
    def source(self, source):
        bl_camera.set_source(self, source)

    @property
    def render_pass(self):
        return bl_camera.get_render_pass(self)

    @render_pass.setter
    def render_pass(self, render_pass):
        bl_camera.set_render_pass(self, render_pass)

    @property
    def render_engine(self):
        return bl_camera.get_render_engine(self)

    @render_engine.setter
    def render_engine(self, render_engine):
        bl_camera.set_render_engine(self, render_engine)

    def render(self):
        '''
        Return a snapshot of the camera's containing scene.

        :rtype: numpy.ndarray
        '''
        if imread:
            path = bl_camera.render(self, 'exr')
            image = imread(path, IMREAD_UNCHANGED)[..., ::-1]
        else:
            path = bl_camera.render(self, 'npy')
            image = load(path)[::-1]
        rmtree(dirname(path))
        return image

    def look_at(self, target, roll=0):
        '''
        Orient the camera towards a point in space.

        :param numpy.ndarray target: 3D spatial location to look at.
        :param float roll: Rotation around the gaze axis, in radians.
        '''
        def norm(v):
            return sqrt(sum(square(v)))

        def normalize(v):
            return array(v, 'd') / norm(v)

        def rotation(axis, angle):
            w = cos(angle / 2)
            xyz = axis / norm(axis) * sin(angle / 2)
            return hstack([w, xyz])

        def compose(rotation_0, rotation_1):
            w0, x0, y0, z0 = rotation_0
            w1, x1, y1, z1 = rotation_1
            w2 = w0 * w1 - x0 * x1 - y0 * y1 - z0 * z1
            x2 = w0 * x1 + x0 * w1 + y0 * z1 - z0 * y1
            y2 = w0 * y1 + y0 * w1 + z0 * x1 - x0 * z1
            z2 = w0 * z1 + z0 * w1 + x0 * y1 - y0 * x1
            return array([w2, x2, y2, z2])

        eye = normalize(target - self.position)
        look_axis = cross((0, 0, -1), eye) if any(eye[:2]) else (1, 0, 0)
        look = rotation(look_axis, arccos(dot((0, 0, -1), eye)))
        pivot = rotation(array((0, 0, -1)), pi/2 - arctan2(*eye[1::-1]) + roll)
        self.rotation = compose(look, pivot)

class DepthSensor(Camera):
    '''
    A camera that reports the depth at each pixel.

    :param dict \**properties: Initial values of instance variables.
    '''
    def __new__(cls, **properties):
        return Camera.__new__(cls, render_pass='z', **properties)

    def render(self):
        '''
        Return a snapshot of the camera's containing scene.

        :rtype: numpy.ndarray
        '''
        return Camera.render(self)[:, :, 0]

class SurfaceNormalSensor(Camera):
    '''
    A camera that reports the surface normal at each pixel.

    :param dict \**properties: Initial values of instance variables.
    '''
    def __new__(cls, **properties):
        return Camera.__new__(cls, render_pass='normal', **properties)

    def render(self):
        '''
        Return a snapshot of the camera's containing scene.

        :rtype: numpy.ndarray
        '''
        return Camera.render(self)[:, :, 0:3]

class VelocitySensor(Camera):
    '''
    A camera that reports the velocity at each pixel.

    :param dict \**properties: Initial values of instance variables.
    '''
    def __new__(cls, **properties):
        return Camera.__new__(cls, render_pass='vector', **properties)

    def render(self):
        '''
        Return a snapshot of the camera's containing scene.

        :rtype: numpy.ndarray
        '''
        return Camera.render(self)[:, :, 0:3]

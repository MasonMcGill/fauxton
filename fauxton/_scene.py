from numpy import array
from _core import BlenderModule, BlenderResource

__all__ = ['Prop', 'Scene', 'read_scene', 'write_scene']

#===============================================================================
# Private Symbols
#===============================================================================

server = BlenderModule('''
    from random import randint

    def create_prop(type_, data):
        prop = bpy.data.objects.new('', data)
        prop['__type__'] = type_
        return prop

    def get_position(prop):
        return list(prop.location)

    def set_position(prop, position):
        prop.location = position

    def get_rotation(prop):
        prop.rotation_mode = 'QUATERNION'
        return list(prop.rotation_quaternion)

    def set_rotation(prop, rotation):
        prop.rotation_mode = 'QUATERNION'
        prop.rotation_quaternion = rotation

    def create_scene(type_):
        scene = bpy.data.scenes.new('')
        scene.world = bpy.data.worlds.new('')
        scene.world.horizon_color = (0, 0, 0)
        scene['__type__'] = type_
        scene['prop_names'] = {}
        scene['prop_keys'] = {}
        return scene

    def get_size(scene):
        return len(scene.objects)

    def prop_names(scene):
        return scene['prop_names'].keys()

    def contains(scene, key):
        return key in scene['prop_names']

    def get_by_key(scene, key):
        name = scene['prop_names'][key]
        return scene.objects[name]

    def set_by_key(scene, key, prop):
        if contains(scene, key):
            scene.objects.unlink(get_by_key(scene, key))
        scene.objects.link(prop)
        scene['prop_names'][key] = prop.name
        scene['prop_keys'][prop.name] = key

    def remove_by_key(scene, key):
        prop = get_by_key(scene, key)
        scene.objects.unlink(prop)
        del scene['prop_names'][key]
        del scene['prop_keys'][prop.name]

    def add(scene, prop):
        def unused_key():
            key = str(randint(0, 2*32))
            return key if key not in scene['prop_names'] else unused_key()
        set_by_key(scene, unused_key(), prop)
        return prop

    def remove(scene, prop):
        remove_by_key(scene['prop_keys'][prop])
        return prop

    def read_scene(path):
        with bpy.data.libraries.load(path) as (src, dst):
            local_names = list(src.objects)
            dst.scenes = [src.scenes[0]]
            dst.objects = src.objects
        scene = dst.scenes[0]
        global_names = [o.name for o in dst.objects]
        scene['prop_names'] = dict(zip(local_names, global_names))
        scene['prop_keys'] = dict(zip(global_names, local_names))
        return scene

    def write_scene(path, scene):
        return NotImplemented
''')

#===============================================================================
# Public Symbols
#===============================================================================

class Prop(BlenderResource):
    'A graphical object that can be added to a scene.'
    blender_type = 'Object'

    def __new__(cls, data=None, **properties):
        result = server.create_prop(cls.blender_type, data)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    @property
    def position(self):
        'The prop\'s spatial location.'
        return array(server.get_position(self))

    @position.setter
    def position(self, position):
        server.set_position(self, list(map(float, position)))

    @property
    def rotation(self):
        'The props\'s rotation quaternion.'
        return array(server.get_rotation(self))

    @rotation.setter
    def rotation(self, rotation):
        server.set_rotation(self, list(map(float, rotation)))

    @property
    def pose(self):
        'The prop\'s position and rotation.'
        return self.position, self.rotation

    @pose.setter
    def pose(self, pose):
        self.position, self.rotation = pose

class Scene(BlenderResource):
    'A collection of graphical objects.'
    blender_type = 'Scene'

    def __new__(cls, **properties):
        result = server.create_scene(cls.blender_type)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    def __len__(self):
        return server.get_size(self)

    def __contains__(self, key):
        return server.contains(self, key)

    def __iter__(self):
        return iter(server.prop_names(self))

    def __getitem__(self, key):
        return server.get_by_key(self, key)

    def __setitem__(self, key, prop):
        server.set_by_key(self, key, prop)

    def __delitem__(self, key):
        server.remove_by_key(self, key)

    def add(self, prop):
        'Add a prop to the scene.'
        return server.add(self, prop)

    def remove(self, prop):
        'Remove a prop from the scene.'
        return server.remove(self, prop)

def read_scene(path):
    'Read a scene from a ".blend" file into memory.'
    return server.read_scene(path)

def write_scene(path, scene):
    'Write a scene in memory to a ".blend" file.'
    return NotImplemented

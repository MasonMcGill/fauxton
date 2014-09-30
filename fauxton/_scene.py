from numpy import array
from _core import BlenderModule, BlenderResource

__name__ = 'fauxton'
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
        scene['global_names'] = {}
        scene['local_names'] = {}
        return scene

    def get_size(scene):
        return len(scene.objects)

    def prop_names(scene):
        return scene['global_names'].keys()

    def contains(scene, name):
        return name in scene['global_names']

    def get_by_name(scene, name):
        global_name = scene['global_names'][name]
        return bpy.data.objects[global_name]

    def set_by_name(scene, name, prop):
        if contains(scene, name):
            scene.objects.unlink(get_by_name(scene, name))
        scene.objects.link(prop)
        scene['global_names'][name] = prop.name
        scene['local_names'][prop.name] = name

    def remove_by_name(scene, name):
        prop = get_by_name(scene, name)
        scene.objects.unlink(prop)
        del scene['global_names'][name]
        del scene['local_names'][prop.name]

    def add(scene, prop):
        def unused_name():
            name = str(randint(0, 2*32))
            return name if name not in scene['global_names'] else unused_name()
        set_by_name(scene, unused_name(), prop)
        return prop

    def remove(scene, prop):
        remove_by_key(scene['local_names'][prop])
        return prop

    def read_scene(path):
        with bpy.data.libraries.load(path) as (src, dst):
            local_names = list(src.objects)
            dst.scenes = [src.scenes[0]]
            dst.objects = src.objects
        scene = dst.scenes[0]
        global_names = [o.name for o in dst.objects]
        scene['global_names'] = dict(zip(local_names, global_names))
        scene['local_names'] = dict(zip(global_names, local_names))
        return scene

    def write_scene(path, scene):
        conflicting_scene = bpy.data.scenes.get('0', None)
        if conflicting_scene: conflicting_scene.name = ''
        old_scene_name = scene.name
        scene.name = '0'

        removed_objects = {}
        for s in bpy.data.scenes[1:]:
            removed_objects[s.name] = list(s.objects)
            [s.objects.unlink(o) for o in s.objects]

        old_object_names = {o: o.name for o in bpy.data.objects}
        for global_name, local_name in scene['local_names'].items():
            bpy.data.objects[global_name].name = local_name
    
        bpy.ops.wm.save_as_mainfile(filepath=path)
        
        for o, name in old_object_names.items():
            o.name = name

        for s in bpy.data.scenes[1:]:
            [s.objects.link(o) for o in removed_objects[s.name]]
    
        if conflicting_scene: conflicting_scene.name = '0'
        scene.name = old_scene_name
  ''')        

#===============================================================================
# Public Symbols
#===============================================================================

class Prop(BlenderResource):
    '''
    A graphical object that can be added to a scene.

    :param BlenderResource data: Resource to wrap.
    :param dict \**properties: Initial values of instance variables.

    :var numpy.ndarray position: 3D spatial location.
    :var numpy.ndarray rotation: 4D rotation quaternion.
    :var tuple pose: `(position, rotation)`.
    '''
    resource_type = 'Object'

    def __new__(cls, data=None, **properties):
        result = server.create_prop(cls.resource_type, data)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    @property
    def position(self):
        return array(server.get_position(self))

    @position.setter
    def position(self, position):
        server.set_position(self, list(map(float, position)))

    @property
    def rotation(self):
        return array(server.get_rotation(self))

    @rotation.setter
    def rotation(self, rotation):
        server.set_rotation(self, list(map(float, rotation)))

    @property
    def pose(self):
        return self.position, self.rotation

    @pose.setter
    def pose(self, pose):
        self.position, self.rotation = pose

class Scene(BlenderResource):
    '''
    A collection of graphical objects.

    :param dict \**properties: Initial values of instance variables.

    Operations defined on a `Scene` `s`:
        ========== =============================================================
        `len(s)`   Return the number of props in `s`.
        `iter(s)`  Return an iterator over the names of props in `s`.
        `n in s`   Return whether a prop is stored in `s` under the name `n`.
        `s[n]`     Return the prop stored in `s` under the name `n`.
        `s[n] = p` Add the prop `p` to `s`, storing it under the name `n`.
        `del s[n]` Remove the prop stored under the name `n` from `s`.
        ========== =============================================================
    '''
    resource_type = 'Scene'

    def __new__(cls, **properties):
        result = server.create_scene(cls.resource_type)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    def __len__(self):
        return server.get_size(self)

    def __iter__(self):
        return iter(server.prop_names(self))

    def __contains__(self, name):
        return server.contains(self, name)

    def __getitem__(self, name):
        return server.get_by_name(self, name)

    def __setitem__(self, name, prop):
        server.set_by_name(self, name, prop)

    def __delitem__(self, name):
        server.remove_by_name(self, name)

    def add(self, prop):
        '''
        Generate a name for a prop, add it to the scene, then return it.

        :param Prop prop: Prop to add.
        :rtype: Prop
        '''
        return server.add(self, prop)

    def remove(self, prop):
        '''
        Remove a prop from the scene, then return it.

        :param Prop prop: Prop to remove.
        :rtype: Prop
        '''
        return server.remove(self, prop)

def read_scene(path):
    '''
    Read a scene from a ".blend" file into memory.

    :param str path: Location on the filesystem.
    :rtype: Scene
    '''
    return server.read_scene(path)

def write_scene(path, scene):
    '''
    Write a scene in memory to a ".blend" file.

    :param str path: Location on the filesystem.
    :param Scene scene: Scene to write.
    '''
    server.write_scene(path, scene)

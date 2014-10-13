from numpy import array
from _core import BlenderModule, BlenderResource

__name__ = 'fauxton'
__all__ = ['Action', 'Prop', 'Scene', 'read_scene', 'write_scene']

#===============================================================================
# Private Symbols
#===============================================================================

bl_prop = BlenderModule('''
    def create(type_, data):
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

    def get_scale(prop):
        return list(prop.scale)

    def set_scale(prop, scale):
        prop.scale = scale

    def get_action(prop):
        prop.rotation_mode = 'QUATERNION'
        return prop.animation_data.action if prop.animation_data else None

    def set_action(prop, action):
        if prop.animation_data is None:
            prop.animation_data_create()
        prop.rotation_mode = 'QUATERNION'
        prop.animation_data.action = action
  ''')

bl_action = BlenderModule('''
    def create(type_):
        action = bpy.data.actions.new('')
        action['__type__'] = type_
        return action

    def get_position(action):
        return action.get('position', [])

    def set_position(action, position):
        action['position'] = position
        for curve in list(action.fcurves):
            if curve.data_path == 'location':
                action.fcurves.remove(curve)
        for i in range(3):
            curve = action.fcurves.new('location', i)
            curve.keyframe_points.add(len(position))
            for j, point in enumerate(position):
                curve.keyframe_points[j].co = point[0], point[1 + i]
                curve.keyframe_points[j].interpolation = 'LINEAR'

    def get_rotation(action):
        return action.get('rotation', [])

    def set_rotation(action, rotation):
        action['rotation'] = rotation
        for curve in list(action.fcurves):
            if curve.data_path == 'rotation_quaternion':
                action.fcurves.remove(curve)
        for i in range(4):
            curve = action.fcurves.new('rotation_quaternion', i)
            curve.keyframe_points.add(len(rotation))
            for j, point in enumerate(rotation):
                curve.keyframe_points[j].co = point[0], point[1 + i]
                curve.keyframe_points[j].interpolation = 'LINEAR'

    def get_scale(action):
        return action.get('scale', [])

    def set_scale(action, scale):
        action['scale'] = scale
        for curve in list(action.fcurves):
            if curve.data_path == 'scale':
                action.fcurves.remove(curve)
        for i in range(3):
            curve = action.fcurves.new('scale', i)
            curve.keyframe_points.add(len(scale))
            for j, point in enumerate(scale):
                curve.keyframe_points[j].co = point[0], point[1 + i]
                curve.keyframe_points[j].interpolation = 'LINEAR'
  ''')

bl_scene = BlenderModule('''
    from random import randint

    def create(type_):
        scene = bpy.data.scenes.new('')
        scene.world = bpy.data.worlds.new('')
        scene.world.horizon_color = (0, 0, 0)
        scene['__type__'] = type_
        scene['global_names'] = {}
        scene['local_names'] = {}
        return scene

    def get_size(scene):
        return len(scene.objects)

    def get_prop_names(scene):
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

    def get_time(scene):
        return scene.frame_current

    def set_time(scene, time):
        scene.frame_current = time

    def read(path):
        with bpy.data.libraries.load(path) as (src, dst):
            local_names = list(src.objects)
            dst.scenes = [src.scenes[0]]
            dst.objects = src.objects
        scene = dst.scenes[0]
        global_names = [o.name for o in dst.objects]
        scene['global_names'] = dict(zip(local_names, global_names))
        scene['local_names'] = dict(zip(global_names, local_names))
        return scene

    def write(path, scene):
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
    A graphical object that can be added to a ``Scene``.

    :param BlenderResource data: Resource to wrap.
    :param dict \**properties: Initial values of instance variables.

    :var numpy.ndarray position: 3D spatial location.
    :var numpy.ndarray rotation: 4D rotation quaternion.
    :var numpy.ndarray scale: 3D scale--1 component for each object-space axis.
    :var tuple pose: `(position, rotation, scale)`.
    :var Action action: Animation currently being performed.
    '''
    resource_type = 'Object'

    def __new__(cls, data=None, **properties):
        result = bl_prop.create(cls.resource_type, data)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    @property
    def position(self):
        return array(bl_prop.get_position(self))

    @position.setter
    def position(self, position):
        bl_prop.set_position(self, list(map(float, position)))

    @property
    def rotation(self):
        return array(bl_prop.get_rotation(self))

    @rotation.setter
    def rotation(self, rotation):
        bl_prop.set_rotation(self, list(map(float, rotation)))

    @property
    def scale(self):
        return array(bl_prop.get_scale(self))

    @scale.setter
    def scale(self, scale):
        bl_prop.set_scale(self, list(map(float, scale)))

    @property
    def pose(self):
        return self.position, self.rotation, self.scale

    @pose.setter
    def pose(self, pose):
        self.position, self.rotation, self.scale = pose

    @property
    def action(self):
        return bl_prop.get_action(self)

    @action.setter
    def action(self, action):
        if not isinstance(action, Action):
            action = Action(action)
        bl_prop.set_action(self, action)

class Action(BlenderResource):
    '''
    A keyframe-based animation that can be applied to a ``Prop``.

    :param dict \**properties: Initial values of instance variables.

    :var numpy.ndarray position: Sequence of (t, x, y, z) keypoints.
    :var numpy.ndarray rotation: Sequence of (t, w, x, y, z) keypoints.
    :var numpy.ndarray scale: Sequence of (t, x, y, z) keypoints.
    '''
    resource_type = 'Action'

    def __new__(cls, **properties):
        result = bl_action.create(cls.resource_type)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    @property
    def position(self):
        return array(bl_action.get_position(self), 'f')

    @position.setter
    def position(self, position):
        bl_action.set_position(self, [list(map(float, e)) for e in position])

    @property
    def rotation(self):
        return array(bl_action.get_rotation(self), 'f')

    @rotation.setter
    def rotation(self, rotation):
        bl_action.set_rotation(self, [list(map(float, e)) for e in rotation])

    @property
    def scale(self):
        return array(bl_action.get_scale(self), 'f')

    @scale.setter
    def scale(self, scale):
        bl_action.set_scale(self, [list(map(float, e)) for e in scale])

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
        result = bl_scene.create(cls.resource_type)
        [setattr(result, k, v) for k, v in properties.items()]
        return result

    def __len__(self):
        return bl_scene.get_size(self)

    def __iter__(self):
        return iter(bl_scene.get_prop_names(self))

    def __contains__(self, name):
        return bl_scene.contains(self, name)

    def __getitem__(self, name):
        return bl_scene.get_by_name(self, name)

    def __setitem__(self, name, prop):
        bl_scene.set_by_name(self, name, prop)

    def __delitem__(self, name):
        bl_scene.remove_by_name(self, name)

    @property
    def time(self):
        return bl_scene.get_time(self)

    @time.setter
    def time(self, time):
        bl_scene.set_time(self, float(time))

    def add(self, prop):
        '''
        Generate a name for a prop, add it to the scene, then return it.

        :param Prop prop: Prop to add.
        :rtype: Prop
        '''
        return bl_scene.add(self, prop)

    def remove(self, prop):
        '''
        Remove a prop from the scene, then return it.

        :param Prop prop: Prop to remove.
        :rtype: Prop
        '''
        return bl_scene.remove(self, prop)

def read_scene(path):
    '''
    Read a scene from a ".blend" file into memory.

    :param str path: Location on the filesystem.
    :rtype: Scene
    '''
    return bl_scene.read(path)

def write_scene(path, scene):
    '''
    Write a scene in memory to a ".blend" file.

    :param str path: Location on the filesystem.
    :param Scene scene: Scene to write.
    '''
    bl_scene.write(path, scene)

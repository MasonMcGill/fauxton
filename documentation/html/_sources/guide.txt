.. currentmodule:: fauxton

User's Guide
============
Fauxton is designed to leverage computer graphics technology--specifically the Blender animation system and the Open Shading Language--for a wide range of computer vision applications. Because of this, Fauxton provides extensible interfaces to Blender and OSL as well as functionality that simplifies common scene manipulation and rendering tasks.

Blender Modules
---------------
Fauxton runs an instance of the Blender animation system in a background process. A `BlenderModule` allows arbitrary Python code to be executed on this Blender server. Functions defined within a `BlenderModule` can be called as if they were defined in a native Python module::

    module = BlenderModule('add = lambda a, b: a + b')
    assert module.add(3, 5) == 8

Blender also has its own Python environment with its own set of importable modules. Blender's internal API can be accessed via the symbol `bpy`::

    module = BlenderModule('count_scenes = lambda: len(bpy.data.scenes)')
    assert isinstance(module.count_scenes(), int)

However, these inter-process function calls are subject to some restrictions. All arguments and return values must be in one of the following formats:

- Python primitive: an instance of `bool`, `int`, `float`, or `str`.
- Sequence: an iterable object composed of transmittable values.
- Structure: a `dict` mapping strings to transmittable values.
- Date: an instance of `datetime.datetime`.
- Binary data: an instance of `xmlrpc.client.Binary`.
- Resource: an instance of `bpy.types.ID` or `BlenderResource`.

Any uncaught exception raised within a `BlenderModule` is automatically converted to a `BlenderError`. The stack trace from the original exception is copied into the message of the `BlenderError`.

Blender Resources
-----------------
The elementary unit of serializable data in Blender (e.g. a mesh, camera, or scene) is called a `datablock <http://wiki.blender.org/index.php/Doc:2.6/Manual/Data_System/Datablocks>`_. Blender's internal API references datablocks via instances of `bpy.types.ID`, while Fauxton references datablocks via instances of `BlenderResource`.

An instance of `bpy.types.ID` returned from a function defined in a `BlenderModule` will automatically be converted to an instance of `BlenderResource` referencing the same datablock::

    module = BlenderModule('get_mesh = lambda: bpy.data.meshes[0]')
    assert isinstance(module.get_mesh(), BlenderResource)

Similarly, an instance of `BlenderResource` passed into such a function as an argument will automatically be converted to an instance of `bpy.types.ID`::

    module = BlenderModule('get_mesh = lambda: bpy.data.meshes[0]'
                           'get_type_name = lambda x: type(x).__name__')
    assert module.get_type_name(module.get_mesh()) == 'Mesh'

Original object return is implemented leaklessly via weak references::

    module = BlenderModule('get_mesh = lambda: bpy.data.meshes[0]')
    assert module.get_mesh() is module.get_mesh()

Customizing Blender Resource Marshalling
----------------------------------------
Every subclass of `BlenderResource` has a `resource_type` field. If it is not defined explicitly, it is set to the subclass' fully qualified name. A subclass of `BlenderResource` can register itself as a wrapper for a particular kind of datablock by setting its `resource_type` field to the unqualified name of a `bpy.types.ID` subclass::

    class LineStyle(BlenderResource):
        resource_type = 'FreestyleLineStyle'

    module = BlenderModule('get_style = lambda: bpy.data.linestyles[0]')
    assert isinstance(module.get_style(), LineStyle)

When a `BlenderModule` function returns an instance of `bpy.types.ID` `x`, it will be translated into an instance of a type whose `resource_type` matches (in order of precedence)...

1) `x['__type__']`, if it is defined, or
2) `x.type`, if `x` is an instance of `bpy.types.Object`, or
3) The name of the an element of `type(x).mro()` (in descending priority).

Item 3 allows a subclass of `BlenderResource` to act as a client-side analogue of a particular subclass of `bpy.types.ID`. Item 1 exists to support marshalling and serialization of all other subclasses of `BlenderResource`. Item 2 allows different types of "Object" datablocks (e.g. "LAMP" and "MESH") to have different wrappers.

Garbage Collection
------------------
Datablocks that exist on the server but aren't being used (directly or indirectly) by the client are automatically garbage-collected between function calls. To prevent a datablock from being garbage-collected, either...

- Maintain a client-side reference to it, as a `BlenderResource`.
- Maintain a server-side reference to it within another datablock that the client has a reference to (e.g. adding it to a scene that is currently being used).
- Set its `use_fake_user` field to `True`.

Garbage collection can be disabled by calling `disable_blender_gc` and reenabled by calling `enable_blender_gc`. A garbage-collection sweep can forced by calling `collect_blender_garbage`.

Scene Manipulation
------------------
A `Prop` is an entity--such as a lamp, mesh, or camera--that influences physically-based rendering. It is the Fauxton analogue of a `bpy.types.Object`. Props have can be moved and re-oriented by assigning values to their `position` and `rotation` fields.

A `Scene` is a collection of props that exist in the same 3-dimensional space. Props can be added to, retrieved from, and removed from a scene by name::

    scene = Scene()
    scene['camera'] = Camera()
    camera = scene['camera']
    del scene['camera']

Props can also be added to or removed from a `Scene` without specifying a name, and a unique name will be generated automatically::

    scene = Scene()
    camera = Camera()
    scene.add(camera)
    scene.remove(camera)

A `Scene` can be read from a ".blend" file by calling `read_scene`. While the ".blend" format supports writing multiple scenes to the same file, `read_scene` only loads the first one into memory. A `Scene` can be written to a ".blend" file by calling `write_scene`.

.. note:: Writing scenes is not yet implemented.

Rendering
---------
A `Camera` is a `Prop` that can produce images of its containing scene. Every `Camera` has a customizable `field_of_view` and `resolution`, and can `render` its view as a NumPy array.

Every `Camera` has a `source` field that can be used to customize its rendering behavior. Specifically, if `source` is the source code of a valid OSL shader, the emissive material described by that shader will replace the material of every `Prop` is the scene during rendering. Custom OSL shaders can be useful to retrive information about a `Scene` that is not present in optical images (e.g. per-pixel depth, reflectivity, or velocity).

For convenience, Fauxton provides `Camera` subclasses with a variety of default value for `source`: `DepthSensor`, `SurfaceNormalSensor`, and `VelocitySensor`.

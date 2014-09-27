.. currentmodule:: fauxton

API Reference
=============

Overview
--------
.. autosummary::
    :nosignatures:

    BlenderModule
    BlenderError
    BlenderResource
    enable_blender_gc
    disable_blender_gc
    collect_blender_garbage
    Prop
    Scene
    read_scene
    write_scene
    Camera
    DepthCamera
    SurfaceNormalCamera
    VelocityCamera

Blender Interoperation
----------------------
.. autoclass:: BlenderModule(source='')
.. autoclass:: BlenderError(message='')
.. autoclass:: BlenderResource( )
.. autofunction:: enable_blender_gc
.. autofunction:: disable_blender_gc
.. autofunction:: collect_blender_garbage

Scene Manipulation
------------------
.. autoclass:: Prop(data=None, **properties)
.. autoclass:: Scene(**properties)
.. autofunction:: read_scene
.. autofunction:: write_scene

Cameras
-------
.. autoclass:: Camera(**properties)
.. autoclass:: DepthCamera(**properties)
.. autoclass:: SurfaceNormalCamera(**properties)
.. autoclass:: VelocityCamera(**properties)

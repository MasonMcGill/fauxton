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
    Action
    Scene
    read_scene
    write_scene
    Camera
    DepthSensor
    SurfaceNormalSensor
    VelocitySensor

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
.. autoclass:: Action(**properties)
.. autoclass:: Scene(**properties)
.. autofunction:: read_scene
.. autofunction:: write_scene

Cameras
-------
.. autoclass:: Camera(**properties)
.. autoclass:: DepthSensor(**properties)
.. autoclass:: SurfaceNormalSensor(**properties)
.. autoclass:: VelocitySensor(**properties)

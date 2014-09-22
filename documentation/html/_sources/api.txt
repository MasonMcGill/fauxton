.. currentmodule:: fauxton

API Documentation
=================

Overview
--------
.. autosummary::
    BlenderError
    BlenderModule
    BlenderResource
    BlenderResourceType
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
.. autoclass:: BlenderError
.. autoclass:: BlenderModule
.. autoclass:: BlenderResource
.. autoclass:: BlenderResourceType
.. autofunction:: enable_blender_gc
.. autofunction:: disable_blender_gc
.. autofunction:: collect_blender_garbage

Scene Manipulation
------------------
.. autoclass:: Prop
.. autoclass:: Scene
.. autofunction:: read_scene
.. autofunction:: write_scene

Cameras
-------
.. autoclass:: Camera
.. autoclass:: DepthCamera
.. autoclass:: SurfaceNormalCamera
.. autoclass:: VelocityCamera

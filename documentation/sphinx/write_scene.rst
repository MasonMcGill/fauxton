Example: Serialization
======================
The following script constructs a scene, writes it to a file, reads it back into memory, and verifies that its structure has been preserved::

    #!/usr/bin/env python
    from os.path import join
    from shutil import rmtree
    from tempfile import mkdtemp
    from fauxton import DepthSensor, Scene, read_scene, write_scene

    #===============================================================================
    # Scene Building
    #===============================================================================

    scene = Scene()
    scene['depth_sensor'] = DepthSensor()
    scene['depth_sensor'].position = (1, 2, 3)

    #===============================================================================
    # Scene Writing
    #===============================================================================

    scene_dir = mkdtemp()
    scene_path = join(scene_dir, 'scene.blend')
    write_scene(scene_path, scene)

    #===============================================================================
    # Scene Reading and File System Cleanup
    #===============================================================================

    scene = read_scene(scene_path)
    rmtree(scene_dir)

    #===============================================================================
    # Scene Inspection
    #===============================================================================

    assert 'depth_sensor' in scene
    assert type(scene['depth_sensor']) is DepthSensor
    assert tuple(scene['depth_sensor'].position) == (1, 2, 3)

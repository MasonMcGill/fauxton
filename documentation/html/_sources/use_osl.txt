Example: Using OSL
==================
The following script reads an existing scene from :download:`a ".blend" file <scene.blend>`, modifies a camera in that scene to use an OSL shader, and renders the image it captures::

    #!/usr/bin/env python
    from os.path import dirname, join
    from matplotlib.pyplot import axis, imshow, show, title
    from fauxton import read_scene

    #===============================================================================
    # Rendering
    #===============================================================================

    scene_path = join(dirname(__file__), 'scene.blend')
    camera = read_scene(scene_path)['Camera']

    camera.source = '''
        shader pattern(output color result = color(0))
          { result = noise("uperlin", 5 * u, 5 * v); }
      '''

    #===============================================================================
    # Visualization
    #===============================================================================

    imshow(camera.render())
    title('Texture Generated with OSL')
    axis('off')
    show()

**Output**:

.. image:: use_osl.png
    :scale: 75%
    :align: center

Example: Scene Building
=======================
The following script constructs a scene from scratch and renders consecutive frames while moving the camera:

::

    #!/usr/bin/env python
    from numpy import cos, pi, sin
    from matplotlib.pyplot import axis, draw, imshow, show, title
    from fauxton import BlenderModule, Camera, Scene

    #===============================================================================
    # Server-Side Procedure Definition
    #===============================================================================

    blender = BlenderModule('''
        def make_triangle():
            vertices = [(-1, 0, -1), (1, 0, -1), (0, 0, 1)]
            triangle = bpy.data.objects.new('', bpy.data.meshes.new(''))
            triangle.data.from_pydata(vertices, [], [(0, 1, 2)])
            return triangle

        def make_point_light(color):
            point_light = bpy.data.objects.new('', bpy.data.lamps.new('', 'POINT'))
            point_light.data.color = color
            return point_light
    ''')

    #===============================================================================
    # Scene Building
    #===============================================================================

    scene = Scene()

    triangle = scene.add(blender.make_triangle())
    red_light = scene.add(blender.make_point_light((1, 0, 0)))
    green_light = scene.add(blender.make_point_light((0, 1, 0)))
    blue_light = scene.add(blender.make_point_light((0, 0, 1)))

    triangle.position = (0, 0, 0)
    red_light.position = (2, -2, -2)
    green_light.position = (0, 2, 2)
    blue_light.position = (-1, -1, 0)

    #===============================================================================
    # Rendering
    #===============================================================================

    camera = scene.add(Camera())

    def render_frame(t):
        radius = 5
        angle = t * pi / 32
        camera.position = (radius * cos(angle), radius * sin(angle), 0)
        camera.look_at(triangle.position)
        return camera.render()

    #===============================================================================
    # Visualization
    #===============================================================================

    plot = imshow([[0]])
    title('Custom Scene')
    axis('off')
    show(block=False)

    for t in range(128):
        plot.set_data(render_frame(t))
        draw()

**Output**:

.. image:: example_3.png
    :align: center
    :scale: 75%

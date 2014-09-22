Rendering a Scene from a File
=============================
The following script reads an existing scene from a ".blend" file and renders 3 versions of the same image: an optical image, a surface normal map, and a depth map:

::

    #!/usr/bin/env python
    from sys import path
    from os.path import dirname, join
    path.append(join(dirname(__file__), '..'))

    from matplotlib.pyplot import axis, imshow, show, subplot, title
    from fauxton import DepthCamera, SurfaceNormalCamera, read_scene

    #===============================================================================
    # Rendering
    #===============================================================================

    scene_path = join(dirname(__file__), 'scene.blend')
    scene = read_scene(scene_path)

    optical_camera = scene['Camera']
    normal_camera = scene.add(SurfaceNormalCamera(pose=optical_camera.pose))
    depth_camera = scene.add(DepthCamera(pose=optical_camera.pose))

    optical_image = optical_camera.render()
    normal_image = normal_camera.render()
    depth_image = depth_camera.render()

    #===============================================================================
    # Visualization
    #===============================================================================

    def show_scaled(image, plot_name):
        image -= image.min()
        image /= image.max()
        title(plot_name)
        axis('off')
        imshow(image)

    subplot(1, 3, 1); show_scaled(optical_image, 'Optical Image')
    subplot(1, 3, 2); show_scaled(normal_image, 'Surface Normals')
    subplot(1, 3, 3); show_scaled(depth_image, 'Depth')
    show()

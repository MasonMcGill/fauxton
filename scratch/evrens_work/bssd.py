# Evren Gokcen
# bssd.py
#
# Description:  This module is the main library containing wrapper functions
#               for the blender game engine.

from bge import logic, events
import random

def keyHit(key_code):
    """Return true if a key has been pressed, and false otherwise."""
    status = logic.keyboard.events[key_code]
    return status == logic.KX_INPUT_JUST_ACTIVATED

def load(path):
    """Load the scene specified by 'path' into the Blender Game Engine."""
    logic.LibLoad(path, "Scene")
    print("loaded")

def replace(old_object, new_object):
    """
    replace: Replace an old mesh object with a new mesh object.
    arguments: old_object: string; The name of the old object.
               new_object: string; The name of the new object.
    return: nothing
    """
    scene = logic.getCurrentScene()
    old = scene.objects[old_object]
    old.replaceMesh(new_object)
    # Print message for debugging purposes.
    print("replaced")

def addCamera(location, velocity):
    """
    addCamera: Add a camera by loading the scene with the pre-created
               cube and camera.
    arguments: location: tuple; The initial location of the camera.
               velocity: tuple; The initial velocity of the camera.
    return: camera: Blender object; The camera just created.
    """
    scene = logic.getCurrentScene()
    # Add the cube, which is the camera's parent object.
    cube = scene.addObject("CubePilot", "BlendApp")
    # Add the camera.
    camera = scene.addObject("CubePilotCamera", "CubePilotCamera")
    # Set the parent-child relationship.
    camera.setParent(cube)
    # Set the initial location of the camera.
    cube.worldPosition = (location)
    cube.worldLinearVelocity = (velocity)
    print("added")
    return camera

def switchCamera(camera):
    """
    switchCamera: Set the specified camera to be the active camera.
    arguments: camera: Blender object; The camera to become active.
    return: nothing
    """
    scene = logic.getCurrentScene()
    scene.active_camera = camera
    print("switched")

def free(file):
    """
    free: Free the specified file from memory.
    arguments: file: string; The file name.
    return: nothing
    """
    logic.LibFree(file)
    print("freed")

def randomPosition(bounds):
    """
    randomPosition: Generate a random 3-tuple representing the position
                        an object.
    arguments: bounds: 6-tuple; Contains the bounds for the position.
                       It should follow this format:
                           (x_min, x_max, y_min, y_max, z_min, z_max)
    return: The generated position.
    """
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    x = random.uniform(x_min, x_max)
    y = random.uniform(y_min, y_max)
    z = random.uniform(z_min, z_max)
    return (x, y, z)

def randomVelocity(bounds):
    """
    randomVelocity: Generate a random 3-tuple representing the velocity
                        an object.
    arguments: bounds: 6-tuple; Contains the bounds for the velocity.
                       It should follow this format:
                           (x_min, x_max, y_min, y_max, z_min, z_max)
    return: The generated velocity.
    """
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    x = random.uniform(x_min, x_max)
    y = random.uniform(y_min, y_max)
    z = random.uniform(z_min, z_max)
    return (x, y, z)

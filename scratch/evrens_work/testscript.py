# Evren Gokcen
# testscript.py
#
# Description: This module is an example of a possible user script.
#              It loads a scene, adds a camera at a random velocity
#              and position, and causes the camera to reset to a new
#              velocity and position each time there is a collision.
#              NOTE: For this demonstration, you have to press enter
#                    each time a scene restarts.

from bge import logic, events
import bssd
import userdata
import time

def main():
    cont = logic.getCurrentController()
    if cont.sensors['Begin'].positive:
        # For debugging.
        print(logic.getCurrentScene())
        # Load the scene to be navigated through, as well as the scene with
        #     the camera.
        bssd.load("/home/evren/SURF/BlendApp/test_scene.blend")
        bssd.load("/home/evren/SURF/BlendApp/cube_camera.blend")
        # Generate a random initial position and velocity for the camera.
        loc = bssd.randomPosition(userdata.SCENE_BOUNDS)
        vel = bssd.randomVelocity(userdata.VELOCITY_BOUNDS)
        # Add the camera and make it active.
        camera = bssd.addCamera(loc, vel)
        bssd.switchCamera(camera)
        # Free the scene from memory.
        bssd.free("cube_camera.blend")
    # Check for a collision.
    if cont.sensors['Collision'].positive:
        # Sleep, just to slow things down for demonstration.
        time.sleep(1)
        # Restart the scene.
        logic.restartGame()
# Evren Gokcen
# resource.py
#
# Description: This is the initial controller that will set up the Blender
#              computer vision application and run the user's script.
#
# Revision History:
# 08/05/14    Evren Gokcen    Initial Revision

from os.path import abspath, dirname
from sys import path
path.append(dirname(abspath(__file__)))

import bge
import userdata

def main(my_cont):
    own = my_cont.owner
    message_sensor = my_cont.sensors["Message"]
    # Run the user script only if you receive a message to do so.
    if message_sensor.positive:
    	# Specify the script and entry point.
        scene = bge.logic.getCurrentScene()
        userscript = scene.objects["UserScript"]
        user_cont = userscript.controllers["UserScript"]
        user_cont.script = userdata.SCRIPT_NAME
        # Send signal for the user script to execute.
        my_cont.activate(my_cont.actuators["RunUserScript"])
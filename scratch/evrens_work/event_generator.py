# Evren Gokcen
# event_generator.py
#
# Description:  This module is a Blender Game Engine Python controller.
#               it takes input from the user and converts it to meaningful
#               events.
#
# Revision History:
# 08/13/14    Evren Gokcen    Initial Revision.

import bge

def main(cont):
    key_sensor = cont.sensors["Keyboard"]
    for key in key_sensor.events:
        if key[1] == 1:
            if key[0] == 13:    # Enter key
                cont.activate(cont.actuators["Execute"])
                
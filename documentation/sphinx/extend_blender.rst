Example: Blender Interoperation
===============================
To enable scene manipulation and rendering, Fauxton runs an instance of Blender in a background process. The following script demonstrates communication with this Blender instance via remote procedure calling::

    #!/usr/bin/env python
    from fauxton import BlenderModule, BlenderResource

    #===============================================================================
    # Remote Procedure Calling
    #===============================================================================

    addition = BlenderModule('''
        def add(a, b):
            return a + b
      ''')

    assert addition.add(3, 5) == 8

    #===============================================================================
    # Working with Built-In Resource Types
    #===============================================================================

    curves = BlenderModule('''
        def create_curve():
        return bpy.data.curves.new('', 'CURVE')

        def set_bevel_depth(curve, depth):
            curve.bevel_depth = depth

        def get_bevel_depth(curve):
            return curve.bevel_depth
      ''')

    curve = curves.create_curve()
    assert type(curve) is BlenderResource

    curves.set_bevel_depth(curve, 3)
    assert curves.get_bevel_depth(curve) == 3

    #===============================================================================
    # Defining wrappers for Built-In Resource Types
    #===============================================================================

    lamps = BlenderModule('''
        def create_lamp(type_):
            lamp = bpy.data.lamps.new('', 'POINT')
            lamp['__type__'] = type_
            return lamp

        def set_color(lamp, color):
            lamp.color = color

        def get_color(lamp):
            return list(lamp.color)
      ''')

    class Lamp(BlenderResource):
        resource_type = 'Lamp'
        color = property(lamps.get_color, lamps.set_color)
        __new__ = lambda t: lamps.create_lamp(t.resource_type)

    lamp = Lamp()
    assert type(lamp) is Lamp

    lamp.color = [0, 0, 1]
    assert lamp.color == [0, 0, 1]

    #===============================================================================
    # Working with Custom Resource Types
    #===============================================================================

    lamp_storage = BlenderModule('''
        lamps = []

        def push(lamp):
            lamps.append(lamp)

        def pop():
            return lamps.pop()
      ''')

    class BlueLamp(Lamp):
        def __new__(cls):
            result = Lamp.__new__(cls)
            result.color = [0, 0, 1]
            return result

    lamp_storage.push(Lamp())
    assert type(lamp_storage.pop()) is Lamp

    lamp_storage.push(BlueLamp())
    assert type(lamp_storage.pop()) is BlueLamp

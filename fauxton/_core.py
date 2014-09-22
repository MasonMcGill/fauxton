from atexit import register as at_exit
from os import devnull
from os.path import exists, join
from shutil import rmtree
from subprocess import Popen
from tempfile import mkdtemp
from time import sleep
from weakref import WeakKeyDictionary, WeakValueDictionary
from xmlrpclib import ServerProxy

__all__ = ['BlenderError', 'BlenderModule', 'BlenderResource',
           'BlenderResourceType', 'enable_blender_gc', 'disable_blender_gc',
           'collect_blender_garbage']

#===============================================================================
# Private Symbols
#===============================================================================

SERVER_SOURCE = '''
from itertools import count
from os.path import dirname, join
from random import randint
from socket import AF_INET, SOCK_STREAM, socket
from textwrap import dedent
from threading import Lock, Thread
from time import sleep
from traceback import format_exc
from xmlrpc.server import SimpleXMLRPCServer
import bpy

#===============================================================================
# Create an XML-RPC server.
#===============================================================================

def is_free(port):
    return socket(AF_INET, SOCK_STREAM).connect_ex(('localhost', port)) != 0

def free_port():
    port = randint(1025, 65535)
    return port if is_free(port) else free_port()

def make_server():
    try:
        port = free_port()
        server = SimpleXMLRPCServer(('localhost', port), allow_none=True)
        base = dirname(__file__)
        with open(join(base, 'port.txt'), 'w+') as f: f.write(str(port))
        open(join(base, 'lock.txt'), 'w+').close()
        return server
    except:
        return make_server()

server = make_server()
active = True

#===============================================================================
# Define resource-management procedures.
#===============================================================================

GC_SLEEP_TIME = 0.1
RESOURCE_COLLECTIONS = {
    'Action': bpy.data.actions,
    'Armature': bpy.data.armatures,
    'Brush': bpy.data.brushes,
    'Camera': bpy.data.cameras,
    'Curve': bpy.data.curves,
    'VectorFont': bpy.data.fonts,
    'GreasePencil': bpy.data.grease_pencil,
    'Group': bpy.data.groups,
    'Image': bpy.data.images,
    'Lamp': bpy.data.lamps,
    'Lattice': bpy.data.lattices,
    'Library': bpy.data.libraries,
    'FreestyleLineStyle': bpy.data.linestyles,
    'Mask': bpy.data.masks,
    'Material': bpy.data.materials,
    'Mesh': bpy.data.meshes,
    'MetaBall': bpy.data.metaballs,
    'MovieClip': bpy.data.movieclips,
    'NodeTree': bpy.data.node_groups,
    'Object': bpy.data.objects,
    'ParticleSettings': bpy.data.particles,
    'Scene': bpy.data.scenes,
    'Screen': bpy.data.screens,
    'Sound': bpy.data.sounds,
    'Speaker': bpy.data.speakers,
    'Text': bpy.data.texts,
    'Texture': bpy.data.textures,
    'WindowManager': bpy.data.window_managers,
    'World': bpy.data.worlds
  }

gc_lock = Lock()
gc_is_enabled = False
active_resources = set()

def get_id(resource):
    def describe_class():
        return ':'.join(t.__name__ for t in type(resource).mro()[-4::-1])
    if '__type__' in resource:
        return resource['__type__'], resource.name
    elif isinstance(resource, bpy.types.Object):
        return describe_class() + ':' + resource.type, resource.name
    else:
        return describe_class(), resource.name

def reference(resource):
    resource_id = get_id(resource)
    active_resources.add(resource_id)
    return resource_id

def dereference(resource_id):
    type_name, resource_name = resource_id
    base_name = type_name.split(':')[0]
    return RESOURCE_COLLECTIONS[base_name][resource_name]

def release(resource_id):
    active_resources.remove(resource_id)

def collect_garbage():
    def collect_assuming_lock():
        garbage_collected = False
        for collection in RESOURCE_COLLECTIONS:
            for resource in collection:
                used_internally = resource.users or resource.use_fake_user
                used_externally = get_id(resource) in active_resources
                if not (used_internally or used_externally):
                    collection.remove(resource)
                    garbage_collected = True
        if garbage_collected:
            collect_assuming_lock()
    with gc_lock:
        collect_assuming_lock()

def enable_gc():
    global gc_is_enabled
    def collect_continuously():
        while gc_is_enabled:
            collect_garbage()
            sleep(GC_SLEEP_TIME)
    if not gc_is_enabled:
        gc_is_enabled = True
        Thread(target=collect_continuously).run()

def disable_gc():
    global gc_is_enabled
    gc_is_enabled = False

#enable_gc()

#===============================================================================
# Provide support for user-defined modules.
#===============================================================================

modules = {}

def new_module_id():
    id_ = randint(0, 2**30)
    return id_ if id_ not in modules else new_module_id()

def demarshall(m_argument):
    tag, value = m_argument
    if tag == 'value':
        return value
    elif tag == 'reference':
        return dereference(value)

def marshall(result):
    if isinstance(result, bpy.types.ID):
        return 'reference', reference(result)
    else:
        return 'value', result

def add_module(source):
    module_id = new_module_id()
    modules[module_id] = {'bpy': bpy}
    exec(dedent(source), modules[module_id])
    return module_id

def remove_module(module_id):
    del modules[module_id]

def call(module_id, function_name, *m_arguments):
    with gc_lock:
        try:
            module = modules[module_id]
            function = module[function_name]
            arguments = list(map(demarshall, m_arguments))
            result = function(*arguments)
            return marshall(result)
        except:
            return 'error', format_exc()

def shut_down():
    global active
    active = False

#===============================================================================
# Start the server.
#===============================================================================

server.register_function(collect_garbage)
server.register_function(enable_gc)
server.register_function(disable_gc)
server.register_function(add_module)
server.register_function(remove_module)
server.register_function(call)
server.register_function(release)
server.register_function(shut_down)

while active:
    server.handle_request()
'''

def start_server():
    base = mkdtemp()
    with open(join(base, 'server.py'), 'w+') as f: f.write(SERVER_SOURCE)
    command = ['blender', '-b', '-P', join(base, 'server.py')]
    Popen(command, stdout=open(devnull, 'w'), stderr=open(devnull, 'w'))
    while not exists(join(base, 'lock.txt')): sleep(.001)
    with open(join(base, 'port.txt')) as f: port = f.read()
    rmtree(base)
    return ServerProxy("http://localhost:%s/" % port, allow_none=True)

server = start_server()
at_exit(server.shut_down)

class Monitor(object):
    def __init__(self, destructor):
        self.destructor = destructor

    def __del__(self):
        try: self.destructor()
        except: pass

resource_types = {}
resources = WeakValueDictionary()
resource_ids = WeakKeyDictionary()
resource_monitors = WeakKeyDictionary()

def reference(resource):
    return resource_ids[resource]

def dereference(resource_id):
    if resource_id in resources:
        return resources[resource_id]
    type_name = resource_id[0]
    while type_name and type_name not in resource_types:
        type_name = type_name.rpartition(':')[0]
    type_ = resource_types.get(type_name, BlenderResource)
    monitor = Monitor(lambda: server.release(resource_id))
    resource = object.__new__(type_)
    resources[resource_id] = resource
    resource_ids[resource] = resource_id
    resource_monitors[resource] = monitor
    return resource

def marshall(argument):
    if argument in resource_ids:
        return 'reference', reference(argument)
    else:
        return 'value', argument

def demarshall(m_result):
    tag, value = m_result
    if tag == 'value':
        return value
    elif tag == 'reference':
        return dereference(tuple(value))
    elif tag == 'error':
        raise BlenderError(value)

def call(module_id, symbol, *arguments):
    m_arguments = map(marshall, arguments)
    m_result = server.call(module_id, symbol, *m_arguments)
    return demarshall(m_result)

#===============================================================================
# Public Symbols
#===============================================================================

class BlenderError(Exception):
    'An error that occurred executing code within Blender.'
    pass

class BlenderModule(object):
    'Custom Blender functionality accessible via remote procedure calling.'

    def __init__(self, source):
        self._id = server.add_module(source)

    def __del__(self):
        try: server.remove_module(self)
        except: pass

    def __getattr__(self, symbol):
        return lambda *x: call(self._id, symbol, *x)

class BlenderResourceType(type):
    'A type providing an interface to Blender resources.'

    def __new__(cls, name, bases, fields):
        explicit_type = fields.pop('blender_type', '') or None
        result = type.__new__(cls, name, bases, fields)
        base_type = getattr(result, 'blender_type', '') or None
        full_name = result.__module__ + '.' + name

        if explicit_type or base_type:
            result.blender_type = explicit_type or (base_type + ':' + full_name)
            resource_types[result.blender_type] = result

        return result

class BlenderResource(object):
    'A resource on the Blender server.'
    __metaclass__ = BlenderResourceType

def enable_blender_gc():
    'Allow the Blender server to automatically free unused resources.'
    server.enable_gc()

def disable_blender_gc():
    'Prevent the Blender server from automatically freeing unused resources.'
    server.disable_gc()

def collect_blender_garbage():
    'Manually free unused Blender resources.'
    server.collect_garbage()

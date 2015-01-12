from atexit import register as at_exit
from os import devnull
from os.path import exists, join, isfile
from shutil import rmtree
from subprocess import Popen
from sys import platform
from tempfile import mkdtemp
from time import sleep
from weakref import WeakKeyDictionary, WeakValueDictionary
from xmlrpclib import ServerProxy

__name__ = 'fauxton'
__all__ = ['BlenderModule', 'BlenderError', 'BlenderResource',
           'enable_blender_gc', 'disable_blender_gc', 'collect_blender_garbage']

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
    resource_types = [t.__name__ for t in type(resource).mro()[-4::-1]]
    if isinstance(resource, bpy.types.Object):
        resource_types.append(resource.type)
    if '__type__' in resource:
        resource_types.append(resource['__type__'])
    return ':'.join(resource_types), resource.name

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
        Thread(target=collect_continuously).start()

def disable_gc():
    global gc_is_enabled
    gc_is_enabled = False

enable_gc()

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
    blender_paths = ['/Applications/blender.app/Contents/MacOS/blender',
                     '/Applications/Blender.app/Contents/MacOS/blender']
    base = mkdtemp()
    with open(join(base, 'server.py'), 'w+') as f: f.write(SERVER_SOURCE)
    blender_path = next(iter(filter(isfile, blender_paths)), 'blender')
    command = [blender_path, '-b', '-P', join(base, 'server.py')]
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
    type_names = resource_id[0].split(':')[::-1] + ['ID']
    best_type_name = next(n for n in type_names if n in resource_types)
    resource = object.__new__(resource_types[best_type_name])
    monitor = Monitor(lambda: server.release(resource_id))
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

class BlenderModule(object):
    '''
    Custom Blender functionality accessible via remote procedure calling.

    :param str source: Python code to be executed.

    Operations defined on a `BlenderModule` `m`:
        =============== ========================================================
        `getattr(m, s)` Access the callable symbol `s` defined within `m`.
        =============== ========================================================
    '''
    def __init__(self, source=''):
        self._id = server.add_module(source)

    def __del__(self):
        try: server.remove_module(self)
        except: pass

    def __getattr__(self, symbol):
        '''
        '''
        return lambda *x: call(self._id, symbol, *x)

class BlenderError(Exception):
    '''
    An error that occurred executing code within a `BlenderModule`.

    :param str message: Description of the error.
    '''
    def __init__(self, message=''):
        Exception.__init__(self, message)

class BlenderResource(object):
    '''
    A resource on the Blender server.
    '''
    resource_type = 'ID'

    class __metaclass__(type):
        def __new__(cls, name, bases, fields):
            result = type.__new__(cls, name, bases, fields)
            if 'resource_type' not in result.__dict__:
                result.resource_type = result.__module__ + '.' + name
            resource_types[result.resource_type] = result
            return result

def enable_blender_gc():
    '''
    Allow the Blender server to automatically free unused resources.
    '''
    server.enable_gc()

def disable_blender_gc():
    '''
    Prevent the Blender server from automatically freeing unused resources.
    '''
    server.disable_gc()

def collect_blender_garbage():
    '''
    Manually free unused Blender resources.
    '''
    server.collect_garbage()

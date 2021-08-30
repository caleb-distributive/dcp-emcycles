import random
import math
import os
import mathutils
import bpy.types
import xml.etree.ElementTree as etree
import xml.dom.minidom as dom

_options = {}
#!exports scene as XML to fp
def export_cycles(fp, scene, inline_textures=False):
    global _options
    _options = {
        'inline_textures': inline_textures
    }

    film = etree.Element('film', {
        'width':str(int(scene.render.resolution_x * scene.render.resolution_percentage / 100.0)),
        'height':str(int(scene.render.resolution_y * scene.render.resolution_percentage / 100.0))
    })

    write(film, fp)

    for node in gen_scene_nodes(scene):
        if node is not None:
            write(node, fp)

    return {'FINISHED'}

#!generates the XML nodes for the background, then every material, and then every object
def gen_scene_nodes(scene):
    written_materials = set()

    yield write_material(scene.world, 'background')

    for object in scene.objects:
        materials = getattr(object.data, 'materials', []) or getattr(object, 'materials', [])
        if materials:
            for material in materials:
                if hash(material) not in written_materials:
                    material_node = write_material(material)
                    if material_node is not None:
                        written_materials.add(hash(material))
                        yield material_node
        elif object.type == 'LIGHT':
            light_shader_node = write_light_shader(object)
            yield light_shader_node

        yield  write_object(object, scene=scene)

def write_light_shader(object):
    node = etree.Element('shader', {
        'name': object.name,
    })

    emission = etree.Element('emission', {
        'name': 'emission',
        'color': '%f %f %f' % (
            object.data.color[0],
            object.data.color[1],
            object.data.color[2]
        ),
        'strength': '%f' % object.data.energy
    })

    node.append(emission)
    node.append(etree.Element('connect', {
        'from':'emission emission',
        'to': 'output surface'
    }))

    return node


# reference: blender_camera.cpp blender_camera_viewplane
def compute_camera(camera, scene):
    width = scene.render.resolution_x * scene.render.resolution_percentage / 100.0
    height = scene.render.resolution_y * scene.render.resolution_percentage / 100.0
    xratio = width * scene.render.pixel_aspect_x
    yratio = height * scene.render.pixel_aspect_y
    if camera.sensor_fit == 'AUTO':
        horizontal_fit = (xratio > yratio)
        sensor_size = camera.sensor_width
    elif camera.sensor_fit == 'HORIZONTAL':
        horizontal_fit = True
        sensor_size = camera.sensor_width
    else:
        horizontal_fit = False
        sensor_size = camera.sensor_height
    if horizontal_fit:
        aspectratio = xratio / yratio
        xaspect = aspectratio
        yaspect = 1.0
    else:
        aspectratio = yratio / xratio
        xaspect = 1.0
        yaspect = aspectratio
    if camera.type == 'ORTHO':
        xaspect = xaspect * camera.ortho_scale / (aspectratio * 2.0)
        yaspect = yaspect * camera.ortho_scale / (aspectratio * 2.0)
        aspectratio = camera.ortho_scale / 2.0
    return sensor_size, aspectratio

def write_camera(camera, scene):
    camera = camera.data

    if camera.type == 'ORTHO':
        camera_type = 'orthographic'
    elif camera.type == 'PERSP':
        camera_type = 'perspective'
    else: # TODO: 'PANO'
        raise Exception('Camera type %r unknown!' % camera.type)

    sensor_size, aspectratio = compute_camera(camera, scene)
    fov = 2.0 * math.atan((0.5 * sensor_size) / camera.lens / aspectratio);

    return etree.Element('camera', {
        'type': camera_type,

        # fabio: untested values. assuming to be the same as found here:
        # http://www.blender.org/documentation/blender_python_api_2_57_release/bpy.types.Camera.html#bpy.types.Camera.clip_start
        'fov': str(math.degrees(fov)),
        'nearclip': str(camera.clip_start),
        'farclip': str(camera.clip_end),
        #'aperturesize': str(0.5 * camera.lens / camera.dof.aperture_fstop), # this is wrong
        'focaldistance': str(camera.dof.focus_distance),
        #'shutteropen':  ??
        #'shutterclose': ??
    })


def write_object(object, scene):
    if object.type == 'MESH':
        node = write_mesh(object, scene)
    elif object.type == 'LIGHT':
        node = write_light(object)
    elif object.type == 'CAMERA':
        node = write_camera(object, scene)
    elif object.type == 'ARMATURE':
        return None
    else:
        raise NotImplementedError('Object type: %r' % object.type)

    node = wrap_in_state(node, object)
    node = wrap_in_transforms(node, object)
    return node



# writes the material/shader of an object
def write_material(material, tag_name='shader'):
    did_copy = False
    if not material.use_nodes:
        did_copy = True
        material = material.copy()
        material.use_nodes = True

    #translates socket name from blender to cycles format (only works for MIX_SHADER?)
    def xlateSocket(typename, socketname):
        for i in xlate:
            if i[0]==typename:
                for j in i[2]:
                    if j[0]==socketname:
                        return j[1]
        return socketname
    
    #translates type from blender to cycles format
    def xlateType(typename):
        for i in xlate:
            if i[0]==typename:
                return i[1]
        return typename.lower()
    
    #returns True if socket is connected to links, False otherwise
    def isConnected(socket, links):
        for link in links:
            if link.from_socket == socket or link.to_socket == socket:
                return True
        return False

    #returns True if node is an output node
    def is_output(node):
        return node.type in ('OUTPUT', 'OUTPUT_MATERIAL', 'OUTPUT_WORLD')

    #returns the index of socket in node, or empty string if none is found
    def socketIndex(node, socket):
        socketindex=0
        countname=0
        for i in node.inputs:
            if i.name == socket.name:
             countname += 1
             if i==socket:
                socketindex=countname
        if socketindex>0:
            if countname>1:
                return str(socketindex)
            else:
                return ''
        countname=0
        for i in node.outputs:
            if i.name == socket.name:
                countname += 1
                if i==socket:
                    socketindex=countname
        if socketindex>0:
            if countname>1:
                return str(socketindex)
        return ''
    #           blender        <--->     cycles
    xlate = ( ("RGB",                   "color",()),
              ("BSDF_DIFFUSE",          "diffuse_bsdf",()),
              ("BSDF_GLOSSY",           "glossy_bsdf",()),
              ("BSDF_TRANSPARENT",      "transparent_bsdf",()),
              ("BUMP",                  "bump",()),
              ("FRESNEL",               "fresnel",()),
              ("MATH",                  "math",()),
              ("MIX_RGB",               "mix",()),
              ("MIX_SHADER",            "mix_closure",(("Shader","closure"),)),
              ("OUTPUT_MATERIAL",       "",()),
              ("SUBSURFACE_SCATTERING", "subsurface_scattering",()),
              ("TEX_IMAGE",             "image_texture",()),
              ("TEX_MAGIC",             "magic_texture",()),
              ("TEX_NOISE",             "noise_texture",()),
              ("TEX_COORD",             "texture_coordinate",()),
            )
    
    node_tree = material.node_tree
    # nodes, links = get_nodes_links(conte#xt)
    nodes, links = node_tree.nodes, node_tree.links

    output_nodes = list(filter(is_output, nodes))

    if not output_nodes:
        return None

    nodes = list(nodes)  # We don't want to remove the node from the actual scene.
    nodes.remove(output_nodes[0])

    shader_name = material.name

    # tag_name is usually 'shader' but could be 'background' for world shaders
    shader = etree.Element(tag_name, { 'name': shader_name })
    
    def socket_name(socket, node):
        # TODO don't do this. If it has a space, don't trust there's
        # no other with the same name but with underscores instead of spaces.
        return xlateSocket(node.type, socket.name.replace(' ', '')) + socketIndex(node, socket)
    
    def shader_node_name(node):
        if is_output(node):
            return 'output'

        return node.name.replace(' ', '_')

    #returns the XML node for Texture, RGB, and Value nodes
    def special_node_attrs(node):
        def image_src(image):
            path = node.image.filepath_raw
            if path.startswith('//'):
                path = path[2:]

            if _options['inline_textures']:
                return { 'src': path }
            else:
                import base64
                w, h = image.size
                image = image.copy()
                newimage = bpy.data.images.new('/tmp/cycles_export', width=w, height=h)
                newimage.file_format = 'PNG'
                newimage.pixels = [pix for pix in image.pixels]
                newimage.filepath_raw = '/tmp/cycles_export'
                newimage.save()
                with open('/tmp/cycles_export', 'rb') as fp:
                    return {
                        'src': path,
                        'inline': base64.b64encode(fp.read()).decode('ascii')
                    }
            
        if node.type == 'TEX_IMAGE' and node.image is not None:
            return image_src(node.image)
        elif node.type == 'RGB':
            color = space_separated_float3(
                node.outputs['Color']
                    .default_value[:3])

            return { 'value': color }
        elif node.type == 'VALUE':
            return {
                'value': '%f' % node.outputs['Value'].default_value
            }

        return {}

    connect_later = []

    #
    def gen_shader_node_tree(nodes):
        for node in nodes:
            node_attrs = { 'name': shader_node_name(node) }
            node_name = xlateType(node.type)

            for input in node.inputs:
                if isConnected(input,links):
                    continue
                if not hasattr(input,'default_value'):
                    continue

                el = None
                sock = None
                if input.type == 'RGBA':
                    el = etree.Element('color', {
                        'value': '%f %f %f' % (
                            input.default_value[0],
                            input.default_value[1],
                            input.default_value[2],
                        )
                    })
                    sock = 'Color'
                elif input.type == 'VALUE':
                    el = etree.Element('value', { 'value': '%f' % input.default_value })
                    sock = 'Value'
                elif input.type == 'VECTOR':
                    pass  # TODO no mapping for this?
                else:
                    print('TODO: unsupported default_value for socket of type: %s', input.type);
                    print('(node %s, socket %s)' % (node.name, input.name))
                    continue

                if el is not None:
                    el.attrib['name'] = input.name + ''.join(
                        random.choice('abcdef')
                        for x in range(5))

                    connect_later.append((
                        el.attrib['name'],
                        sock,
                        node,
                        input
                    ))
                    yield el

            node_attrs.update(special_node_attrs(node))
            yield etree.Element(node_name, node_attrs)

    for snode in gen_shader_node_tree(nodes):
        if snode is not None:
            shader.append(snode)

    for link in links:
        from_node = shader_node_name(link.from_node)
        to_node = shader_node_name(link.to_node)

        from_socket = socket_name(link.from_socket, node=link.from_node)
        to_socket = socket_name(link.to_socket, node=link.to_node)

        shader.append(etree.Element('connect', {
            'from': '%s %s' % (from_node, from_socket.replace(' ', '_')),
            'to': '%s %s' % (to_node, to_socket.replace(' ', '_')),

            # uncomment to be compatible with the new proposed syntax for defining nodes
            # 'from_node': from_node,
            # 'to_node': to_node,
            # 'from_socket': from_socket,
            # 'to_socket': to_socket
        }))

    for fn, fs, tn, ts in connect_later:
        from_node = fn
        to_node = shader_node_name(tn)

        from_socket = fs
        to_socket = socket_name(ts, node=tn)

        shader.append(etree.Element('connect', {
            'from': '%s %s' % (from_node, from_socket.replace(' ', '_')),
            'to': '%s %s' % (to_node, to_socket.replace(' ', '_')),

            # uncomment to be compatible with the new proposed syntax for defining nodes
            # 'from_node': from_node,
            # 'to_node': to_node,
            # 'from_socket': from_socket,
            # 'to_socket': to_socket
        }))

    if did_copy:
        # TODO delete the material we created as a hack to support materials with use_nodes == False
        pass
    return shader


def write_light(object):
    # TODO export light's shader here? Where? UPDATE: DONE above but sloppily

    if object.data.type == 'POINT':
        return etree.Element('light', {
            'type': 'point',
            'P': '0.0 0.0 0.0',
            'size': '%f' % object.data.shadow_soft_size
        })
    elif object.data.type == 'SPOT':
        return etree.Element('light', {
            'type': 'spot',
            'P': '%f %f %f' % (
                object.location[0],
                object.location[1],
                object.location[2]
            ),
            'size': '%f' % object.data.shadow_soft_size,
            'spot_angle': '%f' % object.data.spot_size,
            'spot_smooth': '%f' % object.data.spot_blend #this part may be wrong

        })
    # TODO implement AREA and SUN lights

def write_mesh(object, scene):
    mesh = object.to_mesh()

    # generate mesh node
    nverts = ""
    verts = ""

    P = ' '.join(space_separated_float3(v.co) for v in mesh.vertices)

    for i, f in enumerate(mesh.polygons):
        nverts += str(len(f.vertices)) + " "

        for v in f.vertices:
            verts += str(v) + " "

    return etree.Element('mesh', attrib={'nverts': nverts, 'verts': verts, 'P': P})

def wrap_in_transforms(xml_element, object):
    matrix = object.matrix_world

    if (object.type == 'CAMERA'):
        # In cycles, the camera points at its positive Z axis rather than negative
        mat_trans_to_origin = mathutils.Matrix.Translation(-matrix.to_translation()) - mathutils.Matrix.Identity(4)
        mat_reflectz = mathutils.Matrix.Scale(-1, 4, (0, 0, 1))
        mat_reflectx = mathutils.Matrix.Scale(-1, 4, (1, 0, 0))
        mat_reflect = mat_reflectz @ mat_reflectx
        matrix += mat_trans_to_origin
        matrix = matrix.copy() @ mat_reflect
        matrix -= mat_trans_to_origin

    wrapper = etree.Element('transform', { 
        'matrix': space_separated_matrix(matrix.transposed())
    })
                        
    wrapper.append(xml_element)

    return wrapper

def wrap_in_state(xml_element, object):
    # UNSUPPORTED: Meshes with multiple materials
    if object.type == 'LIGHT':
        state = etree.Element('state', {
            'shader': object.name
        })
        state.append(xml_element)

        return state
    try:
        material = getattr(object.data, 'materials', [])[0]
    except LookupError:
        return xml_element

    state = etree.Element('state', {
        'shader': material.name
    })

    # Trying to handle bpy.ops.object.shade_smooth/shade_flat.
    # The flag is specified per-polygon and can be retrieved by
    #     bpy.data.objects['ObjectName'].data.polygons[0].use_smooth
    # However, it seems that cycles xml api does not support per-polygon smoothness spec:
    #     "smooth" is handled per state, see static void xml_read_state(XMLReadState& state, pugi::xml_node node) (cycles_xml.cpp)
    #     mesh xml does not contain normal spec, see static void xml_read_mesh(const XMLReadState& state, pugi::xml_node node) (cycles_xml.cpp)
    # So for now, use smooth for all mesh
    if object.type == 'MESH':
        state.set('interpolation', 'smooth')

    # create_mesh

    state.append(xml_element)

    return state

def space_separated_float3(coords):
    float3 = list(map(str, coords))
    assert len(float3) == 3, 'tried to serialize %r into a float3' % float3
    return ' '.join(float3)

def space_separated_float4(coords):
    float4 = list(map(str, coords))
    assert len(float4) == 4, 'tried to serialize %r into a float4' % float4
    return ' '.join(float4)

def space_separated_matrix(matrix):
    return ' '.join(space_separated_float4(row) + ' ' for row in matrix)

def write(node, fp):
    # strip(node)
    s = etree.tostring(node, encoding='unicode')
    # s = dom.parseString(s).toprettyxml()
    fp.write(s)
    fp.write('\n')
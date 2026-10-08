"""Native 3D Movie Maker assets. See inc/{tmpl,modl,mtrl,msnd}.h.

CHN2 layout also documented by Ben Stone's MIT pymaginopolis project.
No legacy converter or proprietary SDK is required.
"""
from dataclasses import dataclass, field
import io
import math
from pathlib import Path
import struct
import wave

from PIL import Image, ImageDraw

HEADER = b'\x01\x00\x03\x03'  # little endian, Windows character set
MAX_CHUNK = 0xFFFFFF
MAX_INPUT = 64 * 1024 * 1024


@dataclass
class Chunk:
    tag: str
    number: int
    data: bytes
    name: str = ''
    children: list = field(default_factory=list)  # (tag, number, child ID)


def tag_bytes(tag):
    return tag.encode('ascii')[::-1]


def write_chunks(chunks):
    """Write uncompressed CHN2 with sorted chunk and child indexes."""
    chunks = sorted(chunks, key=lambda c: (c.tag, c.number))
    keys = {(c.tag, c.number) for c in chunks}
    if len(keys) != len(chunks):
        raise ValueError('Duplicate chunk ID')
    parents = {key: 0 for key in keys}
    for c in chunks:
        for tag, num, _ in c.children:
            parents[tag, num] += 1
    body, attrs, index = bytearray(), bytearray(), bytearray()
    for c in chunks:
        if len(c.data) > MAX_CHUNK:
            raise ValueError('Asset exceeds the native 16 MB chunk limit')
        a = bytearray(struct.pack('<4sIIB3sHH', tag_bytes(c.tag), c.number,
                                 128 + len(body), 0 if parents[c.tag, c.number] else 2,
                                 len(c.data).to_bytes(3, 'little'), len(c.children), parents[c.tag, c.number]))
        for tag, num, chid in sorted(c.children, key=lambda k: (k[2], k[0], k[1])):
            a += struct.pack('<4sII', tag_bytes(tag), num, chid)
        if c.name:
            name = c.name.encode('cp1252', errors='replace')[:100]
            a += struct.pack('<HB', 0x303, len(name)) + name + b'\0'
        index += struct.pack('<II', len(attrs), len(a))
        attrs += a + bytes((-len(a)) % 4)
        body += c.data
    idx = HEADER + struct.pack('<IIII', len(chunks), len(attrs), 0xFFFFFFFF, 20) + attrs + index
    end = 128 + len(body) + len(idx)
    head = struct.pack('<4s4sHHHHIIIII92x', b'CHN2', b' SOC', 5, 4, 1, 0x303,
                       end, 128 + len(body), len(idx), end, 0)
    return head + body + idx


def gl(size, items):
    return HEADER + struct.pack('<II', size, len(items)) + b''.join(items)


def gg(fixed_size, items):
    data = b''.join(items)
    offsets, pos = bytearray(), 0
    for item in items:
        offsets += struct.pack('<II', pos, len(item))
        pos += len(item)
    return HEADER + struct.pack('<IIiI', len(items), len(data), -1, fixed_size) + data + offsets


def fixed(value):
    if not math.isfinite(value) or abs(value) > 16000:
        raise ValueError('Model coordinate is outside the supported range')
    return round(value * 65536)


def palette():
    p = Image.new('P', (1, 1))
    p.putpalette((Path(__file__).parent / 'palette.rgb').read_bytes())
    return p


def quantize(image):
    # The scene palette has 256 fixed colors. Transparency becomes opaque black.
    background = Image.new('RGBA', image.size, (0, 0, 0, 255))
    background.alpha_composite(image.convert('RGBA'))
    return background.convert('RGB').quantize(palette=palette(), dither=Image.Dither.FLOYDSTEINBERG)


def load_image(path):
    if Path(path).stat().st_size > MAX_INPUT:
        raise ValueError('Image file exceeds 64 MB')
    with Image.open(path) as source:
        if source.width * source.height > 16_000_000:
            raise ValueError('Image exceeds 16 million pixels')
        image = source.convert('RGBA')
    return image


def texture_chunks(image, number=1):
    # BRender's indexed renderer requires power-of-two textures.
    size = tuple(min(256, max(8, 2 ** math.ceil(math.log2(d)))) for d in image.size)
    tex = quantize(image.resize(size, Image.Resampling.LANCZOS))
    w, h = tex.size
    tmap = HEADER + struct.pack('<hBBhhhhhh', w, 3, 0, 0, 0, w, h, 0, 0) + tex.tobytes()
    mtrl = HEADER + struct.pack('<IHHHBBi', 0xFFFFFF, 0x1999, 0xCCCC, 0, 15, 15, fixed(20))
    return [Chunk('MTRL', number, mtrl, children=[('TMAP', number, 0)]), Chunk('TMAP', number, tmap)]


def thumbnail(root_tag, target_tag, name, image):
    # GOKD: one default location and the standard browser selection command.
    gokd = HEADER + struct.pack('<12i', 0, 0, 0, 0, 10, 0, 0, -1, -1, -1, 50017, -1)
    image = image.copy()
    image.thumbnail((64, 48), Image.Resampling.LANCZOS)
    canvas = Image.new('RGBA', (72, 54), (50, 50, 50, 255))
    canvas.alpha_composite(image.convert('RGBA'), ((72-image.width)//2, (54-image.height)//2))
    data = quantize(canvas).tobytes()
    rows = [bytes((0, 72)) + data[y*72:(y+1)*72] for y in range(54)]
    size = 28 + 108 + sum(map(len, rows))
    mbmp = HEADER + struct.pack('<BBhiiiii', 0, 0, 0, -36, -27, 36, 27, size)
    mbmp += struct.pack('<54h', *map(len, rows)) + b''.join(rows)
    tfc = HEADER + tag_bytes(target_tag) + struct.pack('<I', 1)
    return [Chunk(root_tag, 1, tfc, name, [('GOKD', 1, 0)]),
            Chunk('GOKD', 1, gokd, children=[('MBMP', 1, 65536)]), Chunk('MBMP', 1, mbmp)]


def texture_asset(path, name):
    image = load_image(path)
    return texture_chunks(image), thumbnail('MTTH', 'MTRL', name, image)


def read_obj(path):
    path = Path(path)
    if path.stat().st_size > MAX_INPUT:
        raise ValueError('OBJ file exceeds 64 MB')
    positions, uvs, faces = [], [], []
    for line_no, line in enumerate(path.read_text(encoding='utf-8-sig', errors='replace').splitlines(), 1):
        fields = line.split('#', 1)[0].split()
        if not fields:
            continue
        try:
            if fields[0] == 'v':
                point = tuple(float(v) for v in fields[1:4])
                if len(point) != 3 or not all(math.isfinite(v) for v in point):
                    raise ValueError('Invalid vertex')
                positions.append(point)
            elif fields[0] == 'vt':
                uv = tuple(float(v) for v in fields[1:3])
                if len(uv) != 2 or not all(math.isfinite(v) for v in uv):
                    raise ValueError('Invalid texture coordinate')
                uvs.append(uv)
            elif fields[0] == 'f':
                if len(fields) != 4:
                    raise ValueError('Export the OBJ with triangulation enabled (triangles only)')
                triangle = []
                for token in fields[1:]:
                    indices = token.split('/')
                    def resolve(raw, count):
                        n = int(raw)
                        i = n - 1 if n > 0 else count + n
                        if n == 0 or not 0 <= i < count:
                            raise ValueError('OBJ index is out of range')
                        return i
                    vi = resolve(indices[0], len(positions))
                    ti = resolve(indices[1], len(uvs)) if len(indices) > 1 and indices[1] else None
                    triangle.append((vi, ti))
                faces.append(triangle)
            if len(positions) > 100_000 or len(faces) > 10_000:
                raise ValueError('Use at most 10,000 triangles and 100,000 source vertices')
        except (ValueError, IndexError) as exc:
            raise ValueError(f'OBJ line {line_no}: {exc}') from exc
    if not faces:
        raise ValueError('OBJ has no triangle faces')
    return positions, uvs, faces


def model_asset(path, name, texture=None, height=5.0):
    if not math.isfinite(height) or not 0.01 <= height <= 100:
        raise ValueError('Model size must be between 0.01 and 100')
    positions, uvs, faces = read_obj(path)
    used = {v for face in faces for v, _ in face}
    lo = [min(positions[v][a] for v in used) for a in range(3)]
    hi = [max(positions[v][a] for v in used) for a in range(3)]
    span = max(hi[a]-lo[a] for a in range(3))
    if span <= 1e-10:
        raise ValueError('Model has no size')
    vertices, triangles, lookup = [], [], {}
    for face in faces:
        tri = []
        for key in face:
            if key not in lookup:
                v, t = key
                p = [(positions[v][a] - (lo[a] if a == 1 else (lo[a]+hi[a])/2)) * height/span for a in range(3)]
                uv = uvs[t] if t is not None else (0, 0)
                # OBJ is Y-up; V=0 is the bottom of a texture.
                vertices.append(struct.pack('<5i4BH3h', *(fixed(x) for x in p), fixed(uv[0]), fixed(1-uv[1]),
                                            0, 255, 255, 255, 0, 0, 0, 0))
                lookup[key] = len(vertices)-1
            tri.append(lookup[key])
        triangles.append(struct.pack('<6HIHBB3h2xi', *tri, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0))
    if len(vertices) > 30000:
        raise ValueError('Model exceeds 30,000 vertices after UV seams')
    bmdl = HEADER + struct.pack('<hh10i', len(vertices), len(triangles), *([0]*10))
    bmdl += b''.join(vertices) + b''.join(triangles)
    identity = struct.pack('<12i', 65536,0,0, 0,65536,0, 0,0,65536, 0,0,0)
    children = [(t, 1, 0) for t in ['GLPI', 'GLBS', 'GGCM', 'CMTL', 'BMDL', 'ACTN']]
    content = [Chunk('TMPL', 1, HEADER + struct.pack('<4hI', 0,0,0,0,4), name, children),
               Chunk('GLPI', 1, gl(2, [struct.pack('<h', -1)])),
               Chunk('GLBS', 1, gl(2, [struct.pack('<h', 0)])),
               Chunk('GGCM', 1, gg(4, [struct.pack('<ii', 1, 0)])),
               Chunk('CMTL', 1, HEADER + struct.pack('<i', 0), children=[('MTRL', 1, 0)]),
               Chunk('BMDL', 1, bmdl),
               Chunk('ACTN', 1, HEADER + struct.pack('<i', 8), 'Rest', [('GGCL', 1, 0), ('GLXF', 1, 0)]),
               Chunk('GGCL', 1, gg(8, [struct.pack('<iihh', -1, 0, 0, 0)])),
               Chunk('GLXF', 1, gl(48, [identity]))]
    image = load_image(texture) if texture else Image.new('RGBA', (64, 64), (100, 170, 220, 255))
    content += texture_chunks(image)
    # Draw a projected wireframe preview without depending on a 3D renderer.
    preview = Image.new('RGBA', (144, 108), (45,45,50,255))
    draw = ImageDraw.Draw(preview)
    def project(v):
        x,y,z = positions[v]
        return (72 + ((x-(lo[0]+hi[0])/2) + (z-(lo[2]+hi[2])/2)*0.4)*70/span,
                90 - ((y-lo[1]) + (z-(lo[2]+hi[2])/2)*0.2)*70/span)
    for face in faces[:2000]:
        points = [project(v) for v,_ in face]
        draw.line(points + points[:1], fill=(120,220,240), width=1)
    return content, thumbnail('PRTH', 'TMPL', name, preview)


def sound_asset(path, name):
    import miniaudio
    if Path(path).stat().st_size > MAX_INPUT:
        raise ValueError('Sound file exceeds 64 MB')
    info = miniaudio.get_file_info(str(path))
    if info.duration > 90:
        raise ValueError('Use sounds of 90 seconds or less per pack')
    sound = miniaudio.decode_file(str(path), output_format=miniaudio.SampleFormat.SIGNED16,
                                 nchannels=2, sample_rate=44100)
    output = io.BytesIO()
    with wave.open(output, 'wb') as wav:
        wav.setparams((2, 2, 44100, 0, 'NONE', 'not compressed'))
        wav.writeframes(sound.samples.tobytes())
    data = output.getvalue()
    if len(data) > MAX_CHUNK:
        raise ValueError('Decoded sound exceeds the native 16 MB limit')
    return [Chunk('MSND', 1, HEADER + struct.pack('<iii', 2, 65536, 0), name, [('WAVE', 1, 0)]),
            Chunk('WAVE', 1, data)], [Chunk('SFTH', 1, HEADER + b'DNSM' + struct.pack('<I', 1), name)]

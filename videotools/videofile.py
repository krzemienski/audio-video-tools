
#!python3

import sys
import ffmpeg
import re
import os
import jprops
import shutil

PROPERTIES_FILE = r'E:\Tools\VideoTools.properties'
FFMPEG = r'E:\Tools\VideoTools.properties'

class EncodeSpecs:
    def __init__(self):
        self.vcodec = 'libx264'
        self.acodec = 'libvo_aacenc'
        self.vbitrate = '2048k'
        self.abitrate = '128k'

    def set_vcodec(self, vcodec):
        self.vcodec = vcodec

    def set_acodec(self, acodec):
        self.acodec = acodec
    
    def set_vbitrate(self, bitrate):
        self.vbitrate = bitrate

    def set_abitrate(self, bitrate):
        self.abitrate = bitrate
    
    def set_format(self, fmt):
        self.format = fmt

class VideoFile:
    def __init__(self, filename):
        self.filename = filename
        self.stream = ffmpeg.input(filename)

    def set_profile(self, profile):
        self.profile = profile

    def set_fps(self, fps):
        self.stream = ffmpeg.filter_(self.stream, 'fps', fps=fps, round='up')
    
    def encode(self, target_file, profile):
        # stream = ffmpeg.input(self.filename)
        self.stream = ffmpeg.output(self.stream, target_file, acodec='libvo_aacenc', vcodec='libx264', f='mp4', vr='2048k', ar='128k' )
        self.stream = ffmpeg.overwrite_output(self.stream)

        try:
            ffmpeg.run(self.stream)
        except ffmpeg.Error as e:
            print(e.stderr, file=sys.stderr)
            sys.exit(1)
    
    def aspect(self, aspect_ratio):
        self.stream = ffmpeg.filter_(self.stream, 'fps', aspect=aspect_ratio)

    def scale(self, scale):
        self.stream = ffmpeg.filter_(self.stream, 'scale', size=scale)

    def crop(self, x, y, h, w):
        self.stream = ffmpeg.crop(self.stream, x, y, h, w)

    def get_metadata(self):
        return ffmpeg.probe(self.filename)

    def set_author(self, author):
        self.author = author

    def get_author(self):
        return self.author

    def set_copyright(self, copyright):
        self.copyright = copyright

    def get_copyright(self):
        return self.copyright


def get_size(cmdline):
    m = re.search(r'-s\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_video_codec(cmdline):
    m = re.search(r'-vcodec\s+(\S+)', cmdline)
    if m:
        return m.group(1) 
    m = re.search(r'-c:v\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_audio_codec(cmdline):
    m = re.search(r'-acodec\s+(\S+)', cmdline)
    if m:
        return m.group(1) 
    m = re.search(r'-c:a\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_format(cmdline):
    m = re.search(r'-f\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_audio_bitrate(cmdline):
    m = re.search(r'-ab\s+(\S+)', cmdline)
    if m:
        return m.group(1) 
    m = re.search(r'-b:a\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_video_bitrate(cmdline):
    m = re.search(r'-vb\s+(\S+)', cmdline)
    if m:
        return m.group(1) 
    m = re.search(r'-b:v\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_aspect_ratio(cmdline):
    m = re.search(r'-aspect\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_frame_rate(cmdline):
    m = re.search(r'-r\s+(\S+)', cmdline)
    return m.group(1) if m else ''

def get_params(cmdline):
    found = True
    parms = dict()
    while (found):
        cmdline = re.sub(r'^\s+', '', cmdline) # Remove heading spaces
        m = re.search(r'^-(\S+)\s+([A-Za-z0-9]\S*)', cmdline) # Format -<option> <value>
        if m:
            parms[m.group(1)] = m.group(2)
            print("Found " + m.group(1) + " --> " + m.group(2))
            cmdline = re.sub(r'^-(\S+)\s+([A-Za-z0-9]\S*)', '', cmdline)
        else:
            m = re.search(r'^-(\S+)\s*', cmdline)  # Format -<option>
            if m:
                parms[m.group(1)] = None
                cmdline = re.sub(r'^-(\S+)\s*', '', cmdline)
            else:
                found = False
    return parms

def get_file_extension(filename):
    return re.sub(r'^.*\.', '', filename)
  
def strip_file_extension(filename):
    return re.sub(r'\.[^.]+$', '', filename)

def get_extension(profile):
    with open(PROPERTIES_FILE) as fp:
        properties = jprops.load_properties(fp)
    try:
        extension = properties[profile + '.extension']
    except KeyError:
        extension = properties['default.extension']
    return extension

def build_target_file(source_file, profile, properties):
    try:
        extension = properties[profile + '.extension']
    except KeyError:
        extension = properties['default.extension']
    
    # Strip extension from source file
    target_file = strip_file_extension(source_file) + r'.' + profile + r'.' + extension
    return target_file


def encode(source_file, target_file, profile):
    with open(PROPERTIES_FILE) as fp:
        properties = jprops.load_properties(fp)

    myprop = properties[profile + '.cmdline']
    if target_file is None:
        target_file = build_target_file(source_file, profile, properties)

    stream = ffmpeg.input(source_file)
    parms = get_params(myprop)
    #stream = ffmpeg.output(stream, target_file, acodec=getAudioCodec(myprop), ac=2, an=None, vcodec=getVideoCodec(myprop),  f=getFormat(myprop), aspect=getAspectRatio(myprop), s=getSize(myprop), r=getFrameRate(myprop)  )
    stream = ffmpeg.output(stream, target_file, **parms  )
    # -qscale:v 3  is **{'qscale:v': 3} 
    stream = ffmpeg.overwrite_output(stream)
    # print(ffmpeg.get_args(stream))
    print (source_file + ' --> ' + target_file)
    try:
        ffmpeg.run(stream, cmd=properties['binaries.ffmpeg'], capture_stdout=True, capture_stderr=True)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
        sys.exit(1)

def get_properties():
    try:
        with open(PROPERTIES_FILE) as fp:
            properties = jprops.load_properties(fp)
    except FileNotFoundError:
        properties['binaries.ffmpeg'] = 'ffmpeg'
    return properties

def encode_album_art(source_file, album_art_file):
    profile = 'album_art'
    properties = get_properties()

    myprop = properties[profile + '.cmdline']
    extension = properties[profile + '.extension']
    target_file = source_file + '.' + extension
    #parms = getParams(myprop)
    parms = { 'c': 'copy', 'id3v2_version': '3','metadata:s:v': 'title="Album cover"'} #, 'metadata:s:v': 'comment="Cover (Front)"'}
    stream1 = ffmpeg.input(source_file)
    a1 = stream1['0']
    stream2 = ffmpeg.input(album_art_file)
    a2 = stream2['0']
    stream = ffmpeg.output(a1, a2, target_file, **parms  )
    print("======ARGS======")
    print(ffmpeg.get_args(stream))
    print(ffmpeg.compile(stream))
    print("=================")
    try:
        ffmpeg.run(stream, cmd=properties['binaries.ffmpeg'], capture_stdout=True, capture_stderr=True)
        shutil.copy(target_file, source_file)
    except ffmpeg.Error as e:
        print(e.stderr, file=sys.stderr)
    os.remove(target_file)

def encode_album_art_direct(source_file, album_art_file):
    profile = 'album_art'
    properties = get_properties()
    myprop = properties[profile + '.cmdline']
    target_file = strip_file_extension(source_file) + '.album_art.' + get_file_extension(source_file)

    # ffmpeg -i %1 -i %2 -map 0:0 -map 1:0 -c copy -id3v2_version 3 -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (Front)" %1.mp3
    os.system(properties['binaries.ffmpeg'] + ' -i ' + source_file + ' -i ' + album_art_file \
        + ' -map 0:0 -map 1:0 -c copy -id3v2_version 3 ' \
        + ' -metadata:s:v title="Album cover" -metadata:s:v comment="Cover (Front)" ' \
        + target_file)
    shutil.copy(target_file, source_file)
    os.remove(target_file)

def rescale(in_file, width, height, out_file = None):
    properties = get_properties()
    if out_file is None:
        out_file = strip_file_extension(in_file) + '.' + str(width) + 'x' + str(height) + '.' + get_file_extension(in_file)
    stream = ffmpeg.input(in_file)
    stream = ffmpeg.filter_(stream, 'scale', size=str(width) + ':' + str(height))
    stream = ffmpeg.output(stream, out_file)
    ffmpeg.run(stream, cmd=properties['binaries.ffmpeg'], capture_stdout=True, capture_stderr=True)
    return out_file

def get_file_specs(in_file):
    probe = None
    try:
        probe = ffmpeg.probe(in_file)
    except AttributeError:
        print (dir(ffmpeg))
    return probe

def filelist(rootDir):
    fullfilelist = []
    for dirName, subdirList, fileList in os.walk(rootDir):
        for fname in fileList:
            fullfilelist.append(dirName + r'\\' + fname)
    return fullfilelist

def match_extension(file, regex):
    p = re.compile(regex, re.IGNORECASE)
    if re.search(p, file) is None:
        return False
    else:
        return True

def is_audio_file(file):
    return match_extension(file,  r'\.(mp3|ogg|aac|ac3|m4a|ape)$')

def is_video_file(file):
    return match_extension(file,  r'\.(avi|wmv|mp4|3gp|mpg|mpeg|mkv|ts|mts|m2ts)$')

def is_image_file(file):
    return match_extension(file,  r'\.(jpg|jpeg|png)$')

def to_hms(seconds):
    s = int(re.sub(r'\..*$', '', seconds))
    if re.search(r'\.[5-9]', seconds):
        s = s + 1
    hours = round(s/3600)
    minutes = round(s/60) - hours*60
    secs = s - hours*3600 - minutes*60
    return (hours, minutes, secs)
    
def to_hms_str(seconds):
    hours, minutes, secs = to_hms(seconds)
    return str(hours) + ':' + str(minutes) + ':' + str(secs)

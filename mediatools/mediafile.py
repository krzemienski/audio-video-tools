#!/usr/local/bin/python3

import sys
import platform
import re
import os
import json
import shutil
import jprops
import ffmpeg
import mediatools.utilities as util
import mediatools.options as opt

class FileTypeError(Exception):
    '''Error when passing a non media file'''

class MediaFile:
    '''Media file abstraction
    A media file can be:
    - A video file
    - An audio file
    - An image file'''
    def __init__(self, filename):
        if not util.is_media_file(filename):
            raise FileTypeError('File %s is neither video, audio nor image file' % filename)
        self.type = util.get_file_type(filename)
        self.filename = filename
        self.specs = None
        self.author = None
        self.year =  None
        self.copyright = None
        self.format = None
        self.format_long = None
        self.nb_streams = None
        self.size = None
        self.bitrate = None
        self.duration = None
        self.probe()

    def get_filename(self):
        '''Returns file name'''
        return self.filename

    def get_author(self):
        '''Returns file author'''
        return self.author

    def get_filetype(self):
        '''Returns filetype'''
        return self.type

    def get_year(self):
        '''Returns file year'''
        return self.year

    def get_copyright(self):
        '''Returns file copyright'''
        return self.copyright

    def probe(self):
        '''Returns media file general specs'''
        if self.specs is not None:
            return self.specs
        try:
            util.logger.info('Probing %s with %s', self.filename, util.get_ffprobe())
            self.specs = ffmpeg.probe(self.filename, cmd=util.get_ffprobe())
        except ffmpeg.Error as e:
            util.logger.error("%s error %s", util.get_ffprobe(), e.stderr)
            return None
        self.decode_specs()
        util.logger.debug(util.json_fmt(self.specs))
        return self.specs

    def decode_specs(self):
        self.get_file_specs()

    def get_file_specs(self):
        '''Reads file format specs'''
        self.format = self.specs['format']['format_name']
        if self.format == 'mov,mp4,m4a,3gp,3g2,mj2':
            ext = util.get_file_extension(self.filename)
            if re.match('^(mp4|mov)', ext, re.IGNORECASE):
                self.format = ext.lower()

        self.format_long = self.specs['format']['format_long_name']
        self.nb_streams = int(self.specs['format']['nb_streams'])
        self.size = int(self.specs['format']['size'])
        try:
            self.bitrate = int(self.specs['format']['bit_rate'])
        except KeyError as e:
            util.logger.error("JSON %s has no key %s\n", util.json_fmt(self.specs), e.args[0])
        try:
            self.duration = float(self.specs['format']['duration'])
        except KeyError as e:
            util.logger.error("JSON %s has no key %s\n", util.json_fmt(self.specs), e.args[0])

    def get_file_properties(self):
        '''Returns file properties as dict'''
        self.get_file_specs()
        return {'filename':self.filename, 'type':self.type, 'format':self.format, \
        'nb_streams':self.nb_streams, 'filesize':self.size, 'duration': self.duration, \
        'bitrate':self.bitrate}

    def __get_first_video_stream__(self):
        util.logger.debug('Searching first video stream')
        for stream in self.specs['streams']:
            util.logger.debug('Found codec %s / %s', stream['codec_type'], stream['codec_name'])
            if stream['codec_type'] == 'video' and stream['codec_name'] != 'gif':
                return stream
        return None

    def __get_first_audio_stream__(self):
        util.logger.debug('Searching first audio stream')
        return self.__get_stream_by_codec__('codec_type', 'audio')

    def __get_audio_stream_attribute__(self, attr, stream = None):
        if stream is None:
            stream = self.__get_first_audio_stream__()
        try:
            return stream[attr]
        except KeyError as e:
            util.logger.error("Audio stream %s has no key %s\n", util.json_fmt(stream), e.args[0])

    def __get_video_stream_attribute__(self, attr, stream = None):
        if stream is None:
            stream = self.__get_first_video_stream__()
        try:
            return stream[attr]
        except KeyError as e:
            util.logger.error("Video stream %s has no key %s\n", util.json_fmt(stream), e.args[0])

    def __get_stream_by_codec__(self, field, value):
        util.logger.debug('Searching stream for codec %s = %s', field, value)
        for stream in self.specs['streams']:
            util.logger.debug('Found codec %s', stream[field])
            if stream[field] == value:
                return stream
        return None

    def get_properties(self):
        all_props = self.get_file_properties()
        return all_props

def build_target_file(source_file, profile):
    extension = util.get_profile_extension(profile)
    if extension is None:
        extension = util.get_file_extension(source_file)
    return util.add_postfix(source_file, profile, extension)

def get_crop_filter_options(width, height, top, left):
    # ffmpeg -i in.mp4 -filter:v "crop=out_w:out_h:x:y" out.mp4
    return '-filter:v "crop={0}:{1}:{2}:{3}"'.format(width, height, top, left)

def get_deshake_filter_options(width, height):
    # ffmpeg -i <in> -f mp4 -vf deshake=x=-1:y=-1:w=-1:h=-1:rx=16:ry=16 -b:v 2048k <out>
    return "-vf deshake=x=-1:y=-1:w=-1:h=-1:rx=%d:ry=%d" % (width, height)

def compute_fps(rate):
    ''' Simplifies the FPS calculation '''
    util.logger.debug('Calling compute_fps(%s)', rate)
    if re.match(r"^\d+\/\d+$", rate):
        a, b = re.split(r'/', rate)
        return str(round(int(a)/int(b), 1))
    return rate

def reduce_aspect_ratio(aspect_ratio, height=None):
    ''' Reduces the Aspect ratio calculation in prime factors '''
    if height is None:
        ws, hs = re.split("[:/x]", aspect_ratio)
        w = int(ws)
        h = int(hs)
    else:
        w = aspect_ratio
        h = height
    for n in [2, 3, 5, 7, 11, 13, 17]:
        while w % n == 0 and h % n == 0:
            w = w // n
            h = h // n
    return "%d:%d" % (w, h)

def get_mp3_tags(file):
    from mp3_tagger import MP3File
    if util.get_file_extension(file).lower() != 'mp3':
        raise FileTypeError('File %s is not an mp3 file')
    # Create MP3File instance.
    mp3 = MP3File(file)
    return {'artist' : mp3.artist, 'author' : mp3.artist, 'song' : mp3.song, 'title' : mp3.song, \
        'album' : mp3.album, 'year' : mp3.year, 'track' : mp3.track, 'genre' : mp3.genre, 'comment' : mp3.comment}

def concat(target_file, file_list):
#    ffmpeg -i opening.mkv -i episode.mkv -i ending.mkv \
#  -filter_complex "[0:v] [0:a] [1:v] [1:a] [2:v] [2:a] concat=n=3:v=1:a=1 [v] [a]" \
#  -map "[v]" -map "[a]" output.mkv
    util.logger.info("Concatenating %s", str(file_list))
    cmd = util.build_ffmpeg_file_list(file_list)
    cmd = cmd + '-filter_complex "'
    for i in range(len(file_list)):
        cmd = cmd + ('[%d:v] [%d:a] ' % (i, i))
    cmd = cmd + 'concat=n=%d:v=1:a=1 [v] [a]" -map "[v]" -map "[a]" %s' % (len(file_list), target_file)
    util.run_ffmpeg(cmd)

def strip_media_options(options):
    strip = {}
    for k in options:
        if k not in opt.M2F_MAPPING:
            strip[k] = options[k]
    util.logger.debug("stripped media options = %s", str(strip))
    return strip

def strip_ffmpeg_options(options):
    strip = {}
    for k in options:
        if k not in opt.F2M_MAPPING:
            strip[k] = options[k]
    util.logger.debug("stripped ffmpeg options = %s", str(strip))
    return strip

def build_ffmpeg_options(options):
    cmd = ''
    for k, v in options.items():
        if options[k] is None or k not in opt.M2F_MAPPING:
            continue
        if options[k] is False:
            continue
        if options[k] is True:
            cmd = cmd + " -%s" % (opt.M2F_MAPPING[k])
        else:
            cmd = cmd + " -%s %s" % (opt.M2F_MAPPING[k], v)
    util.logger.debug("ffmpeg options = %s", cmd)
    return cmd


def build_video_filters_options(filters):
    cmd = ''
    for f in filters:
        if f is not None:
            cmd += '-vf "%s" ' % f
    return cmd.strip()

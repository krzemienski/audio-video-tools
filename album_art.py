#!python

import videotools.filetools, videotools.videofile
import sys
import os

DEFAULT_RESCALING = '512x512'

def file_album_art(filelist, image_file):
    for file in filelist:
        if videotools.filetools.is_audio_file(file):
            print('Encoding audio file %s' % file)
            videotools.videofile.encode_album_art(file, image_file, **{'scale':DEFAULT_RESCALING})

def dir_album_art(directory):
    filelist = videotools.filetools.filelist(directory)
    for file in filelist:
        if videotools.filetools.is_image_file(file):
            album_art_file = file

    if album_art_file is None:
        print('Album Art image file not found')
    else:
        print('Encoding Album Art image file %s' % album_art_file)
    for file in filelist:
        if album_art_file is not None and videotools.filetools.is_audio_file(file):
            print('Encoding audio file %s' % file)
            videotools.videofile.encode_album_art(file, album_art_file, **{'scale':DEFAULT_RESCALING})
        elif os.path.isdir(file):
            dir_album_art(file)

filelist = []
album_art_file = None
for file in sys.argv:
    if os.path.isdir(file):
        dir_album_art(file)
    elif videotools.filetools.is_image_file(file):
        album_art_file = file
    else:
        filelist.append(file)
if album_art_file is None:
    print("No image file found")
else:
    file_album_art(filelist, album_art_file)

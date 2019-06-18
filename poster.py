#!/usr/local/bin/python3

import sys
import os
import argparse
import mediatools.utilities as util
import mediatools.audiofile as audio
import mediatools.imagefile as image

DEFAULT_RESCALING = '512x512'

def filelist_poster(filelist, bg, margin):
    image.posterize(filelist, None, bg, margin)

def dir_poster(directory, bg, margin):
    filelist = util.filelist(directory)
    filelist_poster(filelist, bg, margin)

parser = argparse.ArgumentParser(description='Image shaker')
parser.add_argument('-i', '--inputfiles', nargs='+', required=True, help='Inputd file to posterize')
parser.add_argument('-o', '--outputfile', required=False, help='Output file to create')
parser.add_argument('-c', '--color', required=False, default='black', help='Background color')
parser.add_argument('-p', '--poster_layout', required=False, default=0, help='Layout of the poster')
parser.add_argument('-g', '--debug', required=False, default=0, help='Debug level')
parser.add_argument('-m', '--margin', required=False, default=5, help='Global margin')
parser.add_argument('-l', '--left', required=False, default=0, help='Right margin')
parser.add_argument('-r', '--right', required=False, default=0, help='Left margin')
parser.add_argument('-t', '--top', required=False, default=0, help='Top margin')
parser.add_argument('-b', '--bottom', required=False, default=0, help='Bottom margin')

args = parser.parse_args()

util.set_debug_level(args.debug)

margin=5

dir_list = []
if os.path.isdir(args.inputfiles[0]):
    dir_poster(args.inputfiles[0], args.color, args.margin)
elif len(args.inputfiles) > 0:
    filelist_poster(args.inputfiles, args.color, args.margin)

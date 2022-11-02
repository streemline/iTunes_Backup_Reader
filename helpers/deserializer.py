#
# Plist Deserializer, from NSKeyedArchive to normal plist 
# Copyright (c) 2018  Yogesh Khatri <yogesh@swiftforensics.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You can get a copy of the complete license here:
#  <http://www.gnu.org/licenses/>.
#
# Script Name  : DeSerializer.py
# Author       : Yogesh Khatri
# Last Updated : Nov 12 2019
# Purpose      : NSKeyedArchive plists (such as .SFL2 files) are stored as 
#                serialized data, which is machine readable but not human
#                readable. This script will convert NSKeyedArchive binary 
#                plists into normal plists.
# Usage        : deserializer.py input_plist_path
#                Output will be saved in same location with _deserialised.plist 
#                appended to filename.
# Requirements : 
#                Python3.x
#                biplist (Get it with pip3 install biplist)
#                ccl_bplist
#
# Note: This will not work with python 2.xx

import biplist
import helpers.ccl_bplist as ccl_bplist
import os
import sys
import traceback

def recurseCreatePlist(plist, root, object_table):
    if isinstance(root, dict):
        for key, value in root.items():
            if key == '$class': 
                continue
            v = None
            if isinstance(value, ccl_bplist.BplistUID):
                v2 = ccl_bplist.NSKeyedArchiver_convert(object_table[value.value], object_table)
                if isinstance(v2, dict):
                    v = {}
                    recurseCreatePlist(v, v2, object_table)
                elif isinstance(v2, list):
                    v = []
                    recurseCreatePlist(v, v2, object_table)
                else:
                    v = v2
            elif isinstance(value, list):
                v = []
                recurseCreatePlist(v, value, object_table)
            elif isinstance(value, dict):
                v = {}
                recurseCreatePlist(v, value, object_table)
            else:
                v = value
            plist[key] = v
    else: # must be list
        for value in root:
            v = None
            if isinstance(value, ccl_bplist.BplistUID):
                v2 = ccl_bplist.NSKeyedArchiver_convert(object_table[value.value], object_table)
                if isinstance(v2, dict):
                    v = {}
                    recurseCreatePlist(v, v2, object_table)
                elif isinstance(v2, list):
                    v = []
                    recurseCreatePlist(v, v2, object_table)
                else:
                    v = v2
            elif isinstance(value, list):
                v = []
                recurseCreatePlist(v, value, object_table)
            elif isinstance(value, dict):
                v = {}
                recurseCreatePlist(v, value, object_table)
            else:
                v = value
            plist.append(v)

def getRootElementNames(f):
    ''' The top element is usually called "root", but sometimes it is not!
        Hence we retrieve the correct name here. In some plists, there is
        more than one top element, this function will retrieve them all.
    '''
    roots = []
    try:
        plist = biplist.readPlist(f)
        if top_element := plist.get('$top', None):
            roots = list(top_element.keys())
        else:
            print('$top element not found! Not an NSKeyedArchive?')
    except Exception as ex:
        print('Had an exception (error) trying to read plist using biplist')
        traceback.print_exc()
    return roots

def process_nsa_plist(input_path, f):
    '''Returns a deserialized plist. Input is NSKeyedArchive'''
    global use_as_library
    try:
        if not use_as_library:
            print(f'Reading file .. {input_path}')
        ccl_bplist.set_object_converter(ccl_bplist.NSKeyedArchiver_common_objects_convertor)
        plist = ccl_bplist.load(f)
        ns_keyed_archiver_obj = ccl_bplist.deserialise_NsKeyedArchiver(plist, parse_whole_structure=True)

        root_names = getRootElementNames(f)
        top_level = []

        for root_name in root_names:
            root = ns_keyed_archiver_obj[root_name]
            if not use_as_library:
                print(f'Trying to deserialize binary plist $top = {root_name}')
            if isinstance(root, dict):
                plist = {}
                recurseCreatePlist(plist, root, ns_keyed_archiver_obj.object_table)
                if root_name.lower() != 'root':
                    plist = { root_name : plist }
            elif isinstance(root, list):
                plist = []
                recurseCreatePlist(plist, root, ns_keyed_archiver_obj.object_table)
                if root_name.lower() != 'root':
                    plist = { root_name : plist }
            else:
                plist = { root_name : root }

            if len(root_names) == 1:
                top_level = plist
            else: # > 1
                top_level.append(plist)

    except Exception as ex:
        print('Had an exception (error)')
        traceback.print_exc()

    return top_level

usage = '\r\nDeserializer.py   (c) Yogesh Khatri 2018 \r\n'\
        'This script converts an NSKeyedArchive plist into a normal deserialized one.\r\n\r\n'\
        'Usage: python.exe deserializer.py input_plist_path \r\n'\
        ' Example: deserializer.py com.apple.preview.sfl2 \r\n\r\n'\
        'If successful, the resulting plist will be created in the same folder and will have _unserialized appended to its name.\r\n'

use_as_library = True

def main():
    global usage
    global use_as_library
    use_as_library = False
    if sys.version_info.major == 2:
        print('ERROR-This will not work with python2. Please run again with python3!')
        return
    argc = len(sys.argv)

    if argc < 2 or sys.argv[1].lower() == '-h':
        print(usage)
        return

    input_path = sys.argv[1]
    if not os.path.exists(input_path):
        print('Error, file does not exist! Check file path!\r\n')
        print(usage)
        return

    # All OK, process the file now
    try:
        with open(input_path, 'rb') as f:
            deserialised_plist = process_nsa_plist(input_path, f)
            output_path = f'{input_path}_deserialized.plist'
            print(f'Writing out .. {output_path}')
            biplist.writePlist(deserialised_plist, output_path)
    except Exception as ex:
        print('Had an exception (error)')
        traceback.print_exc()

    print('Done !')

if __name__ == "__main__":
    main()     

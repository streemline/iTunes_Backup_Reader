'''
   Copyright (c) 2019 Jack Farley
   This file is part of iTunes_Backup_Reader
   Usage or distribution of this software/code is subject to the
   terms of the GNU GENERAL PUBLIC LICENSE.
   plist_parser.py
   ------------
'''

from biplist import *
from helpers import writer
from helpers.structs import sinfHelper, frpdHelper
import os
import sys



'''Makes sure each plist exists'''
def checkPaths(status_plist_path, manifest_plist_path, info_plist_path, logger, input_dir):
    '''Check existance of Status.plist'''
    if os.path.isfile(status_plist_path):
        logger.debug("Found Status.plist")
    else:
        logger.warning(f"Status.plist not found in: {input_dir}")
        logger.warning("The Status.plist isn't required, but you will have a loss of data")
        status_plist_path = None

    '''Check existance of Manifest.plist'''
    if os.path.isfile(manifest_plist_path):
        logger.debug("Found Manifest.plist")
    else:
        logger.error(f"Manifest.plist not found in: {input_dir}... Exiting")
        sys.exit()

    '''Check existance of Info.plist'''
    if os.path.isfile(info_plist_path):
        logger.debug("Found Info.plist")
    else:
        logger.error(f"Info.plist not found in: {input_dir}... Exiting")
        sys.exit()

def readApps(apps, info_plist, logger):

    app_dict = []

    for single_app in apps:

        app = apps.get(single_app)

        iTunesBinaryPlist = app.get('iTunesMetadata', {})

        iTunesPlist = readPlistFromString(iTunesBinaryPlist)

        '''Find Apple ID & Purchase Date'''
        downloadInfo = iTunesPlist.get('com.apple.iTunesStore.downloadInfo', {})
        accountInfo = downloadInfo.get('accountInfo', {})

        '''Find full name of person associated with Apple ID from ApplicationSINF'''
        binarySinf = app.get('ApplicationSINF', {})

        '''Gets users full name from SINF'''
        name = sinfHelper(binarySinf, logger)

        if name == "":
            logger.debug("No full name found for: " + iTunesPlist.get('itemName', '')
                          + " This means it could be sideloaded")
            sideloaded = True
        else:
            sideloaded = False

        app_dict.append((info_plist.get('Device Name', ''),
            info_plist.get('Serial Number', ''),
            iTunesPlist.get('itemName', ''),
            accountInfo.get('AppleID', ''),
            name,
            downloadInfo.get('purchaseDate', ''),
            sideloaded,
            iTunesPlist.get('bundleVersion', ''),
            iTunesPlist.get('is-auto-download', ''),
            iTunesPlist.get('is-purchased-redownload', ''),
            iTunesPlist.get('artistName', ''),
            iTunesPlist.get('softwareVersionBundleId', '')))

    return app_dict


def backupReader(info_plist, manifest_plist, status_plist, logger):

    iTunesPrefsPlist = info_plist.get('iTunes Files', {})
    if binaryFrpd := iTunesPrefsPlist.get('iTunesPrefs', ''):
        user_comps = frpdHelper(binaryFrpd, logger)
    else:
        user_comps = ""
        logger.debug("No FRPD data found")


    lockdown = manifest_plist.get('Lockdown', {})

    if status_plist is None:
        status_date = ""
        is_full_backup = ""
        status_version = ""
    else:
        status_date = status_plist.get('Date', '')
        is_full_backup = status_plist.get('IsFullBackup', '')
        status_version = status_plist.get('Version', '')

    return [
        info_plist.get('Device Name', ''),
        info_plist.get('Product Name', ''),
        info_plist.get('Product Type', ''),
        info_plist.get('Phone Number', ''),
        lockdown.get('ProductVersion', ''),
        status_date,
        info_plist.get('Last Backup Date', ''),
        user_comps,
        manifest_plist.get('WasPasscodeSet', ''),
        manifest_plist.get('IsEncrypted', ''),
        info_plist.get('GUID', ''),
        info_plist.get('ICCID', ''),
        info_plist.get('IMEI', ''),
        info_plist.get('MEID', ''),
        info_plist.get('Serial Number', ''),
        is_full_backup,
        status_version,
        info_plist.get('iTunes Version', '')]


def readPlists(status_plist_path, manifest_plist_path, info_plist_path, logger, output_dir):


    status_plist = (
        readPlist(status_plist_path)
        if os.path.exists(status_plist_path)
        else None
    )

    manifest_plist = readPlist(manifest_plist_path)
    info_plist = readPlist(info_plist_path)



    apps = []
    allApps = info_plist.get('Applications', '')
    not_detailed_apps = manifest_plist.get('Applications', '')

    '''Remove duplicate apps in manifest.plist from info.plist'''
    for app in allApps:
        if app in not_detailed_apps:
            not_detailed_apps.pop(app)

    not_detailed_app_dict = [
        (
            "N/A",
            "N/A",
            not_detailed_apps[app]['CFBundleIdentifier'],
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
            "N/A",
        )
        for app in not_detailed_apps
    ]

    if len(allApps) == 0:
        logger.debug("No applications found in the Info.plist. Detailed app data won't be available")
    else:
        apps = readApps(allApps, info_plist, logger)






    bkps = backupReader(info_plist, manifest_plist, status_plist, logger)

    for app in not_detailed_app_dict:
        apps.append(app)
    return bkps, apps



'''Start parsing each plist'''
def parsePlists(input_dir, output_dir, out_type, logger):

    '''Get paths for each plist'''
    status_plist_path = os.path.join(input_dir, "Status.plist")
    manifest_plist_path = os.path.join(input_dir, "Manifest.plist")
    info_plist_path = os.path.join(input_dir, "Info.plist")

    '''Checks paths of plists'''
    checkPaths(status_plist_path, manifest_plist_path, info_plist_path, logger, input_dir)

    '''Read the three plists'''
    backups, apps = readPlists(status_plist_path, manifest_plist_path, info_plist_path, logger, output_dir)

    writer.startWrite(backups, apps, output_dir, out_type, logger)
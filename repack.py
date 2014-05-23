#! /usr/local/bin/python

import argparse
import os
import subprocess
import shutil
import urllib2
import json

DEVNULL = open(os.devnull, 'wb')
log_outfile_name = "repack.log"
LOG_OUTFILE = open(log_outfile_name, 'wb')
scriptpath = os.path.dirname(os.path.realpath(__file__))
apktool_path = os.path.join(scriptpath, 'libs', 'apktool-cli.jar')

def remove_old(path):
    try:
        shutil.rmtree(path)
    except OSError:
        pass

def unpack(apk):
    print "Unpacking."
    p = subprocess.Popen(['java', '-jar', apktool_path, 'd', '-f', apk], stdout=LOG_OUTFILE)
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')

def repack(path):
    print "Repacking"
    p = subprocess.Popen(['java', '-jar', apktool_path, 'b', path], stdout=LOG_OUTFILE)
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')

def sign(path):
    print "Signing"
    apk_repacked_path = path + '/dist/' + path.rsplit('/', 1)[1] + '.apk'
    args = ['jarsigner', '-verbose', '-sigalg', 'SHA1withRSA', '-digestalg', 'SHA1', '-storepass', 'asdfasdf', '-keystore', os.path.join(scriptpath,'debug.keystore'), apk_repacked_path, 'android']
    p = subprocess.Popen(args, stdout=LOG_OUTFILE)
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')
    print "Wrote " + apk_repacked_path

def replace_trigger(path, trigger):
    xml_path = path + '/res/values/strings.xml'
    xml_data = open(xml_path).read().replace('wear a script', trigger).replace('>WearScript<', '>WearScript(%s)<' % trigger)
    open(xml_path, 'w').write(xml_data)

def replace_manifest_package(path, gist):
    manifest_path = path + '/AndroidManifest.xml'
    manifest_data = open(manifest_path).read()
    manifest_data = manifest_data.replace('.dappervision.', '.dappervision_%s.' % gist)
    open(manifest_path, 'w').write(manifest_data)

def replace_smali_files(path, gist):
    if not os.path.exists(path + '/smali/com/dappervision'):
        print('Warning: smali folder not found')
        return
    for root, dirs, files in os.walk(path):
        if root.find('/dappervision/') != -1:
            for file in files:
                file = os.path.join(root, file)
                data = open(file).read().replace('dappervision', 'dappervision_%s' % gist)
                open(file, 'w').write(data)
    shutil.move(path + '/smali/com/dappervision', path + '/smali/com/dappervision_%s' % gist)

def boot_permission(path):
    manifest_path = path + '/AndroidManifest.xml'
    dev_perm ='<uses-permission android:name="com.google.android.glass.permission.DEVELOPMENT"/>'
    boot_perm ='<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>'
    manifest_data = open(manifest_path).read()
    manifest_data = manifest_data.replace(boot_perm, '').replace(dev_perm, dev_perm + boot_perm)
    open(manifest_path, 'w').write(manifest_data)

def gist_url(gistId):
    return "https://api.github.com/gists/%s" % gistId

# TODO: check if get_gist succeeds
def get_gist(gistId, dest_dir):
    response = urllib2.urlopen(gist_url(gistId))
    text = response.read()
    gistInfo = json.loads(text)
    cwd = os.getcwd();
    newDir = os.path.join(cwd, dest_dir, gistId)
    if not os.path.exists(newDir): os.makedirs(newDir)
    for file in gistInfo['files'].keys():
        fileContents = urllib2.urlopen(gistInfo['files'][file]['raw_url'])
        with open(os.path.join(newDir,file), 'w') as f:
            print "Writing %s" % os.path.join(newDir,file)
            f.write(fileContents.read())

def main():
    parser = argparse.ArgumentParser(description='Package a gist into a self-contained apk.')
    parser.add_argument('apk')
    parser.add_argument('--trigger')
    parser.add_argument('gist')
    parser.add_argument('--boot', action='store_true')
    parser.add_argument('--no_package_name_change', action='store_true')
    parser.add_argument('--exclude_gist', action='store_true', help='Do not include gist files in package')
    args = parser.parse_args()
    apk = os.path.abspath(args.apk)
    path = os.path.abspath(apk.rsplit('.', 1)[0])
    gist = args.gist
    remove_old(path)
    print "For detailed output see logfile " + log_outfile_name
    unpack(apk)
    if args.trigger:
        print "Using trigger phrase '%s'" % args.trigger
        replace_trigger(path, args.trigger)
    if not args.no_package_name_change:
        print "Changing package name to com.dappervision_%s.wearscript" % gist
        replace_manifest_package(path, gist)
        replace_smali_files(path, gist)
    if args.boot:
        boot_permission(path)
    if not args.exclude_gist:
        print "Calling get_gist"
        get_gist(gist, os.path.join(path, 'assets'))
    else:
        print "Not calling get_gist"
    repack(path)
    sign(path)
    LOG_OUTFILE.close()

if __name__ == '__main__':
    main()

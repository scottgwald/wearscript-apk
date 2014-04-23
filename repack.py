import argparse
import os
import subprocess
import shutil


def remove_old(path):
    try:
        shutil.rmtree(path)
    except OSError:
        pass

def unpack(apk):
    p = subprocess.Popen(['java', '-jar', 'libs/apktool-cli.jar', 'd', '-f', apk])
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')

def repack(path):
    p = subprocess.Popen(['java', '-jar', 'libs/apktool-cli.jar', 'b', path])
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')

def sign(path):
    apk_repacked_path = path + '/dist/' + path.rsplit('/', 1)[1] + '.apk'
    args = ['jarsigner', '-verbose', '-sigalg', 'SHA1withRSA', '-digestalg', 'SHA1', '-storepass', 'asdfasdf', '-keystore', 'debug.keystore', apk_repacked_path, 'android']
    p = subprocess.Popen(args)
    r = p.wait()
    if r:
        raise RuntimeError('An error occurred, note that this requires Java 7')

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
                data = open(file).read().replace('/dappervision/', '/dappervision_%s/' % gist)
                open(file, 'w').write(data)
    shutil.move(path + '/smali/com/dappervision', path + '/smali/com/dappervision_%s' % gist)

def boot_permission(path):
    manifest_path = path + '/AndroidManifest.xml'
    dev_perm ='<uses-permission android:name="com.google.android.glass.permission.DEVELOPMENT"/>'
    boot_perm ='<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED"/>'
    manifest_data = open(manifest_path).read()
    manifest_data = manifest_data.replace(boot_perm, '').replace(dev_perm, dev_perm + boot_perm)
    open(manifest_path, 'w').write(manifest_data)

def main():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('apk')
    parser.add_argument('--trigger')
    parser.add_argument('gist')
    parser.add_argument('--boot', action='store_true')
    args = parser.parse_args()
    apk = os.path.abspath(args.apk)
    path = os.path.abspath(apk.rsplit('.', 1)[0])
    gist = args.gist
    remove_old(path)
    unpack(apk)
    if args.trigger:
        replace_trigger(path, args.trigger)
    replace_manifest_package(path, gist)
    replace_smali_files(path, gist)
    if args.boot:
        boot_permission(path)
    repack(path)
    sign(path)

if __name__ == '__main__':
    main()

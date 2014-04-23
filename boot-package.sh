#! /bin/bash

# author: Scott Greenwald (github.com/scottgwald) 
# project: WearScript
# license: Apache 2.0 

# first arg is name of apk
# second arg is new trigger phrase
#
# REQUIRES:
#  jar
#    aapt
#  jarsigner
#  keystore file: debug.keystore

#
# CHECK IF COMMAND LINE ARGUMENTS ARE PRESENT
#
if [[ $# > 2 ]]
then
    echo "There are "$#" command line arguments present."
else
    echo "There are "$#" command line arguments present, but I need 3."
    echo "Try including the name of the WearScript apk, a new trigger phrase, and package naming string."
    exit
fi

#
# UNPACK AND THEN REPACK
#
export SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
java -jar $SCRIPTPATH/libs/apktool-cli.jar d -f $1

#
# CHANGE TRIGGER PHRASE
#
# replace string "wear a script" with $2 second commandline argument
export name=$1
export truncatedName=${name:0:${#name}-4}
pathToXml=$truncatedName/res/values/strings.xml
export sedCmd="sed -i .back 's/wear a script/"$2"/g' "$pathToXml
eval $sedCmd
rm $pathToXml.back

#
# CHANGE PACKAGE NAME IN MANIFEST
#
export newPackageSegment=dappervision_$3
export sedCmd="sed -i .back 's/dappervision/"$newPackageSegment"/g' "$truncatedName"/AndroidManifest.xml"
echo $sedCmd
eval $sedCmd

#
# ADD BOOT PERMISSION IN MANIFEST
#
export DEV_PERM='<uses-permission android:name="com.google.android.glass.permission.DEVELOPMENT"\/>'
export BOOT_PERM='<uses-permission android:name="android.permission.RECEIVE_BOOT_COMPLETED" \/>'
export sedCmd="sed -i .back 's/"$DEV_PERM"/"$DEV_PERM$BOOT_PERM"/g' "$truncatedName"/AndroidManifest.xml"
eval $sedCmd

#
# CHANGE PACKAGE NAME IN SMALI FILES
#

# replace instances of "dappervision" with new string
export replaceCmd="find . -iname '*.smali' | xargs sed -i .back 's/dappervision/"$newPackageSegment"/g'" 
eval $replaceCmd
# remove sed's backup files
find $truncatedName -iname '*.back' | xargs rm

#
# MOVE FOLDER IN SMALI DIRECTORY TREE
#

mv $truncatedName/smali/com/dappervision $truncatedName/smali/com/$newPackageSegment

#
# repack
java -jar $SCRIPTPATH/libs/apktool-cli.jar b $truncatedName

#
# VERIFY THE FILE WAS THERE AND IS NEW 
#
export pathToNewApk=$truncatedName/dist/$name
echo "Details of new apk: "
echo `ls -l $pathToNewApk`

#
# SIGN THE RESULTING FILE
#

# debug.keystore is file, assumed to be in current directory
export newName=$truncatedName-renamed.apk

jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore $SCRIPTPATH/debug.keystore $pathToNewApk android
cp $pathToNewApk $newName

#
# INSTALL NEW APK
#

adb install -r $newName


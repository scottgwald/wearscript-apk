#! /bin/bash

# first arg is name of apk
# second arg is new trigger phrase
#
# REQUIRES:
#  apktool
#    aapt
#  jarsigner
#  keystore file: debug.keystore

#
# CHECK IF COMMAND LINE ARGUMENTS ARE PRESENT
#
if [[ $# > 1 ]]
then
    echo "There are "$#" command line arguments present."
else
    echo "There are "$#" command line arguments present, but I need 2."
    echo "Try including the name of the WearScript apk and a new trigger phrase."
    exit
fi

#
# UNPACK AND THEN REPACK
#

export name=$1
export truncatedName=${name:0:${#name}-4}
apktool d -f $name

# replace string "wear a script" with $2 second commandline argument
pathToXml=$truncatedName/res/values/strings.xml
tmp="tmp.xml"
export sedCmd="sed 's/wear a script/"$2"/g' "$pathToXml" > "$tmp
eval $sedCmd
cp $tmp $pathToXml
rm $tmp

# repack
apktool b $truncatedName

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
jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore debug.keystore $pathToNewApk android
cp $pathToNewApk $name

#
# UNINSTALL DIFFERENTLY-SIGNED APK, INSTALL NEW ONE
#
adb uninstall com.dappervision.wearscript
adb install $name

echo `which aapt`

#! /usr/local/bin/python

import urllib2
import json
import argparse
import os

def gist_url(gistId):
	return "https://api.github.com/gists/%s" % gistId

def get_gist(gistId, dest_dir):
	# gistInfo = json.parse(urllib.urlretrieve(gist_url(gistId)))
	print gist_url(gistId)
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
    parser = argparse.ArgumentParser(description='Grab and save a gist by id.')
    parser.add_argument('gistId')
    parser.add_argument('--dest_dir')
    args = parser.parse_args();
    dest_dir = "" if args.dest_dir == None else args.dest_dir
    get_gist(args.gistId, dest_dir);

if __name__ == '__main__':
    main()


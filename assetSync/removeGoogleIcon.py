#! python
import os, fnmatch, filecmp
import shutil
from optparse import OptionParser

UNITYPROJECT = '/unityproject/Assets/exported_assets'
ARTSOURCE_PATH = '/Google Drive/Card Heroes/Art/Assets'
ARTSOURCE_TYPES = ['/chibi','/hd_spine','/mainmenu','/card','/environment']

def findGoogleIcon(path):
    print "fineGoogleIcon in :" + path
    for assetpath,dirs, files in os.walk(os.path.abspath(path)):
        #add a thing for dir == export
        for f in files:
            if fnmatch.fnmatch(f, 'Icon*'):
                iconToDelete = os.path.join(assetpath,f)
                print "removing:"+  iconToDelete
                os.remove(iconToDelete)

def main():

    useage = "useage: removeGoogleIcon.py [options] arg"
    parser = OptionParser(useage)

    (options, args) = parser.parse_args()

    scriptpath = os.getcwd()
    searchpath = scriptpath + UNITYPROJECT
    findGoogleIcon(searchpath)

if __name__ == "__main__":
    main()

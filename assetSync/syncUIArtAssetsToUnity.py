#! python
import os, fnmatch, filecmp
import shutil
import argparse

UNITYPROJECT = '/unityproject/Assets/ui/assets'
ARTSOURCE_PATH = '/Google Drive/Card Heroes/Art/Assets/UI'

class spriteasset(object):
     def __init__(self,path,files,verbose):
        object.__init__(self)
        self.path = path
        self.exportFiles = files
        for x in self.exportFiles:
             if x.startswith('Icon'):
                 self.exportFiles.remove(x)
        self.name = self.exportFiles[0]
        self.type = path.split('/')[-2]
        self.group= path.split('/')[-1]
        if verbose: self.spew()

     def spew(self):
        print "found AssetName:"+self.name + " of type:" + self.type
        print self.path
        for f in self.exportFiles:
            print self.group+"/"+f

     def copyExportFilesToUnity(self,unityPath):
        for exportfile in self.exportFiles:
            exportfilepath = os.path.join(self.path,exportfile)
            unityassetdir = os.path.join(unityPath,self.type,self.group)
            if not os.path.exists(unityassetdir): os.makedirs(unityassetdir)
            unityfilepath = os.path.join(unityassetdir, exportfile)
            if not os.path.exists(unityfilepath) or not filecmp.cmp(unityfilepath,exportfilepath):
                 print "copying "+exportfile+" to assetpipe:"+unityfilepath
                 shutil.copy(exportfilepath,unityfilepath)



#end of spriteasset class
def findSpriteAssets(artPath,args):
    print "findSpriteAssets in :" + artPath
    searchMatches = []
    for assetpath,dirs, files in os.walk(os.path.abspath(artPath)):
        for f in files:
            if fnmatch.fnmatch(f, '*.png'):
                searchMatches.append(spriteasset(assetpath,[f],args.verbose))
    return searchMatches

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

    parser = argparse.ArgumentParser(prog= 'syncUIArtsAssetsToUnity.py')
    parser.add_argument('-v','--verbose', dest = 'verbose', action='store_true', default = False,  help = 'the script is noisy-ier')

    args = parser.parse_args()
    print args.verbose

    scriptpath = os.getcwd()
    homedir = os.getenv('HOME')
    spritesearchpath = homedir + ARTSOURCE_PATH
    exportPath = scriptpath + UNITYPROJECT

    sprites = findSpriteAssets(spritesearchpath,args)

    for sprite in sprites:
        sprite.copyExportFilesToUnity(exportPath)

    findGoogleIcon(exportPath)

if __name__ == "__main__":
    main()

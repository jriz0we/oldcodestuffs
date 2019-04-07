import os, fnmatch, filecmp
import shutil
import argparse

UNITYPROJECT = '/unityproject/Assets/exported_assets'
ARTSOURCE_PATH = '/Google Drive/Card Heroes/Art/Assets'
SPINE_TYPES = ['/chibi','/hd_spine','/mainmenu','/environment','/spell']
SPRITE_TYPES = ['/card','/store','/hud_icons','/social','/stamps']



class prefabasset(object):
    def __init__(self,path,files,verbose):
        object.__init__(self)
        self.path = path
        self.exportFiles = files
        for x in self.exportFiles:
            if x.startswith('Icon'):
                self.exportFiles.remove(x)
            if x.startswith('.DS_Store'):
                self.exportFiles.remove(x)
            if x.endswith('.atlas.txt'):
                self.name = x.split(('.'))[0]
        #self.name = path.split('/')[-3]
        self.type = path.split('/')[-5]
        if verbose: self.spew()

    def spew(self):
        print ("AssetName:"+self.name + " of type:" + self.type)
        print (self.path)
        for f in self.exportFiles:
            print(f)


    def copyPrefabExportFilesToUnity(self,unityPath):
        for exportfile in self.exportFiles:
            if exportfile.startswith('Icon'):continue
            exportfilepath = os.path.join(self.path,exportfile)
            unityfilepath = os.path.join(unityPath,self.type,self.name,exportfile)
            unityassetdir = os.path.join(unityPath,self.type,self.name)
            if not os.path.exists(unityassetdir):
                os.mkdir(unityassetdir)
            if not os.path.exists(unityfilepath) or not filecmp.cmp(unityfilepath,exportfilepath):
                print ("copying "+exportfile+" to assetpipe:" + unityfilepath)
                shutil.copy(exportfilepath,unityfilepath)

#end of prefab asset class

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
        if verbose: self.spew()

     def spew(self):
        print ("AssetName:"+self.name + " of type:" + self.type)
        print (self.path)
        for f in self.exportFiles:
            print(f)

     def copyExportFilesToUnity(self,unityPath):
        for exportfile in self.exportFiles:
            exportfilepath = os.path.join(self.path,exportfile)
            unityassetdir = os.path.join(unityPath,self.type)
            unityfilepath = os.path.join(unityassetdir, exportfile)
            if not os.path.exists(unityfilepath) or not filecmp.cmp(unityfilepath,exportfilepath):
                 print ("copying "+exportfile+" to assetpipe:"+unityfilepath)
                 shutil.copy(exportfilepath,unityfilepath)



#end of spriteasset class

def findSpineExports(artPath,args):
    print ("findSpineExports in :" + artPath)
    searchMatches = []
    for assetpath,dirs, files in os.walk(os.path.abspath(artPath)):
        #add a thing for dir == export
        for f in files:
            if fnmatch.fnmatch(f, '*.atlas.txt'):
                name=f.split(('.'))[0]+('.')
                #print(name)
                subfiles = [fn for fn in files if name in fn]
                #print(subfiles)
                searchMatches.append(prefabasset(assetpath,subfiles,args.verbose))
    return searchMatches

def findSpriteAssets(artPath,args):
    print ("findSpriteAssets in :" + artPath)
    searchMatches = []
    for assetpath,dirs, files in os.walk(os.path.abspath(artPath)):
        for f in files:
            if fnmatch.fnmatch(f, '*.png'):
                searchMatches.append(spriteasset(assetpath,[f],args.verbose))
    return searchMatches

def findGoogleIcon(path):
     print ("fineGoogleIcon in :" + path)
     for assetpath,dirs, files in os.walk(os.path.abspath(path)):
         #add a thing for dir == export
         for f in files:
             if fnmatch.fnmatch(f, 'Icon*'):
                 iconToDelete = os.path.join(assetpath,f)
                 print ("removing:"+  iconToDelete)
                 os.remove(iconToDelete)

parser = argparse.ArgumentParser(prog= 'syncArtsExportsToUnity.py')
parser.add_argument('-v','--verbose', dest = 'verbose', action='store_true', default = False,  help = 'the script is noisy-ier')

args = parser.parse_args()

scriptpath = os.getcwd()
homedir = os.getenv('HOME')
spinesearchpath = homedir + ARTSOURCE_PATH + '/SpineAssets'
spritesearchpath = homedir + ARTSOURCE_PATH + '/SpriteAssets'
exportPath = scriptpath + UNITYPROJECT

for spinetype in SPINE_TYPES:
    searchpath = spinesearchpath + spinetype
    spineAssets = findSpineExports(searchpath,args)
    for prefab in spineAssets:
        prefab.copyPrefabExportFilesToUnity(exportPath)

for spritetype in SPRITE_TYPES:
    searchpath = spritesearchpath + spritetype
    sprites = findSpriteAssets(searchpath,args)
    for sprite in sprites:
        sprite.copyExportFilesToUnity(exportPath)

#findGoogleIcon(exportPath)



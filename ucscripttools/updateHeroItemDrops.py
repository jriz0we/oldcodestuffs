#! python
import os, fnmatch, re
from optparse import OptionParser
from tempfile import mkstemp
from shutil import move


InGameList = ['BlackPanther','BlackWidow','Cable','CaptainAmerica','Colossus',
'Cyclops','Daredevil','Deadpool','EmmaFrost', 'Hawkeye','Hulk','HumanTorch',
'IronMan','JeanGrey','MsMarvel','Punisher','RocketRaccoon','ScarletWitch',
'SpiderMan','Storm','Thing','Thor','Wolverine']

ToBeAddedList = ['SquirrelGirl','LukeCage','Loki','Gambit','GhostRider']

def FindHeroItemDrops(userpath, pattern, Hero):
    patternMatches = []
    searchMatches = []
    for path, dirs, files in os.walk(os.path.abspath(userpath)):
        for filename in fnmatch.filter(files, pattern):
            filepath = os.path.join(path, filename)
            if Hero in filepath:
                patternMatches.append(filepath)
                print 'found:',filepath 
    return patternMatches

def CreateNewChangeList(description):
    "Create a new changelist and returns the changelist number as a string"
    p4in, p4out = os.popen2("p4 changelist -i")
    p4in.write("change: new\n")
    p4in.write("description: " + description)
    p4in.close()
    changelist = p4out.readline().split()[1]
    return changelist


def P4AddFile(fpath, changelist = ""):
    """Open a file for add, 
    if a changelist is passed in then open it in that list"""
    if not fpath: return
    cmd = "p4 add "
    if changelist:
        cmd += " -c " + changelist + " "
    ret = os.popen(cmd + fpath).readline().strip()
    if not ret.endswith("opened for add"):
        print "Couldn't open", fpath, "for add:"
        print ret
        raise ValueError

def P4EditFile(file, changelist = ""):
    """Open a file for edit, 
    if a changelist is passed in then open it in that list"""
    cmd = "p4 edit "
    if changelist:
        cmd += " -c " + changelist + " "
    ret = os.popen(cmd + file).readline().strip()
    if not ret.endswith("opened for edit"):
        print "Couldn't open", file, "for edit:"
        print ret
        raise ValueError

def UpdateSkeletalMeshPath(filepath, Hero):
    searches = "SkeletalMesh=SkeletalMesh'Item_Drops_A.CostumeDrops.|SkeletalMesh=SkeletalMesh'Item_Drops_A."
    replace = "SkeletalMesh=SkeletalMesh'Item_Drops_"+Hero+"."
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(filepath)
    # newLines = replace.split('\n')
    for line in old_file:
        new_file.write(re.sub(searches,replace,line))
        #new_file.write(line.replace(search, replace))
    #close temp file
    new_file.close()
    os.close(fh)
    old_file.close()
    #Remove original file
    os.remove(filepath)
    #Move new file
    move(abs_path, filepath)
    return filepath





def main():
    usage = "usage: updateHeroItemDrops.py  [options] arg"
    parser = OptionParser(usage)




    (options, args) = parser.parse_args()
    #find itemdrop uc files
    #look for pattern based on naming convention, replacing Hero names in the pattern(s)
    searchpath = os.getcwd()
    #@TODO loop to create templates patterns
    pattern = 'MarvelItem_Armor_*.uc'
    mychangelist = None
    description = "updateHeroItemDrops automated changelist"
    if not mychangelist: mychangelist = CreateNewChangeList (description)
    for heroName in InGameList+ToBeAddedList:
        print heroName
        heroDrops = FindHeroItemDrops(searchpath, pattern, heroName)
        for drop in heroDrops:
            P4EditFile(drop,mychangelist)
            UpdateSkeletalMeshPath(drop, heroName)




if __name__ == "__main__":
    main()


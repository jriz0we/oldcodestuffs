#! python
import os, fnmatch
from optparse import OptionParser
from tempfile import mkstemp
from shutil import move


InGameList = ['BlackPanther','BlackWidow','Cable','CaptainAmerica','Colossus',
'Cyclops','DareDevil','Deadpool','EmmaFrost', 'Hawkeye','Hulk','HumanTorch',
'IronMan','JeanGrey','MsMarvel','Punisher','RocketRaccoon','ScarletWitch',
'SpiderMan','Storm','Thing','Thor','Wolverine']

ToBeAddedList = ['SquirrelGirl','Nova','LukeCage']

def FindTemplateMatches(userpath, templateName):
    for path, dirs, files in os.walk(os.path.abspath(userpath)):
        for filename in fnmatch.filter(files, templateName):
            filepath = os.path.join(path, filename)
            return filepath

 
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

def CreateEmoteFromTemplate(template, emoteName, animName):

    newEmotePath = template.replace('EmoteHeroEmoteName',emoteName)
    #if the emote exists, dont proceed
    if os.path.isfile(newEmotePath): return
    replacements = {'EmoteHeroEmoteName':emoteName,'animationName':animName}
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(template)
    # newLines = replace.split('\n')
    #replace class
    for line in old_file:
        for i, j in replacements.iteritems():
            line = line.replace(i,j)
        new_file.write(line)
    #close temp file
    new_file.close()
    os.close(fh)
    old_file.close()
    #Move new file
    move(abs_path, newEmotePath)
    return newEmotePath

def main():
    usage = "usage: newEmoteUCForAllHeroes.py  [options] arg"
    parser = OptionParser(usage)

    parser.add_option("-e","--emoteName", dest = "emote",
                     help ="New Emote name")

    parser.add_option("-a","--animation", dest = "anim",
                     help ="animation name string")

    (options, args) = parser.parse_args()
    #determine user input
    if not (options.emote) and not (options.anim):
        parser.error("must specifiy emote name and animation")
    
    print "creating new emote uc files from %s with %s " % \
        (options.emote, options.anim)

    searchpath = os.getcwd()
    mychangelist = None

    template = FindTemplateMatches(searchpath,'EmoteHeroEmoteName.uc')
    newEmotes = []
    
    for hero in InGameList:
        newEmotes.append('Emote'+hero+options.emote)
        print newEmotes[-1]   
    
    
    description = "newEmoteUCForAllHeroes automated changelist"
        
    if not mychangelist:
        mychangelist = CreateNewChangeList (description)

    for each in newEmotes:
        newEmoteFile = CreateEmoteFromTemplate(template, each , options.anim)
        P4AddFile(newEmoteFile,mychangelist)



if __name__ == "__main__":
    main()


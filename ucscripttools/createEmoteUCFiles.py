#! python
import os, fnmatch
from optparse import OptionParser
from tempfile import mkstemp
from shutil import move

def FindSearchMatches(userpath, filePattern, search):
    patternMatches = []
    searchMatches = []
    for path, dirs, files in os.walk(os.path.abspath(userpath)):
        for filename in fnmatch.filter(files, filePattern):
            filepath = os.path.join(path, filename)
            patternMatches.append(filepath)
    for match in patternMatches:
        if search in open(match).read():
            searchMatches.append(match)
    
    return searchMatches

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

def ReplaceInFile(filepath, search, replace):

    newEmotePath = filepath.replace(search,replace)
    if os.path.isfile(newEmotePath): return
    #Create temp file
    fh, abs_path = mkstemp()
    new_file = open(abs_path,'w')
    old_file = open(filepath)
    # newLines = replace.split('\n')
    for line in old_file:
        new_file.write(line.replace(search, replace))
    #close temp file
    new_file.close()
    os.close(fh)
    old_file.close()
    #Move new file
    newEmotePath = filepath.replace(search,replace)
    move(abs_path, newEmotePath)
    return newEmotePath

def main():
    usage = "usage: createEmoteUCFiles.py  [options] arg"
    parser = OptionParser(usage)

    parser.add_option("-r","--replace", dest = "replace",
                     help ="New Character Name")


    (options, args) = parser.parse_args()
    #determine user input
    if not (options.replace):
        parser.error("must specifiy search and replace flags")
    
    print "creating new emote uc files from %s with %s " % \
        ('Hulk', options.replace)

    searchpath = os.getcwd()
    mychangelist = None
    # if options.changelist: mychangelist = options.changelist
    #start doing stuff
    #create default changelist
    pattern = 'EmoteNightCrawler*.uc'
    search = 'EmoteLukeCage'
    matchingFiles = FindSearchMatches(searchpath, pattern, search)
    
    # for filematch in matchingFiles:
        # print filematch

    if matchingFiles:
        description = "createEmoteUCFiles automated changelist"
        
        if not mychangelist:
            mychangelist = CreateNewChangeList (description)

        for match in matchingFiles:
            newEmote = ReplaceInFile(match, search, options.replace)
            P4AddFile(newEmote,mychangelist)
            print newEmote



if __name__ == "__main__":
    main()


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

def ReplaceInFile(filepath, search, replace):
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
    #Remove original file
    os.remove(filepath)
    #Move new file
    move(abs_path, filepath)

def main():
    usage = "usage: massSearchAndReplaceUC.py  [options] arg"
    parser = OptionParser(usage)
    parser.add_option("-c", "--changelist", dest="changelist",
                      help="specify the p4 changelist")
    
    parser.add_option("-f", "--file", dest="filename",
                      help="read data from specific FILENAME")
    parser.add_option("-d", "--dir", dest="directory",
                      help="search files in specific DIRECTORY")

    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose")

    parser.add_option("-q", "--quiet",
                      action="store_false", dest="verbose")

    parser.add_option("-p","--filepattern", dest ="pattern",
                     help ="read data from files beginning with PREFIX")
    parser.add_option("-s","--search", dest = "search",
                     help ="search pattern to find in files")
    parser.add_option("-r","--replace", dest = "replace",
                     help ="pattern to replace matches with search\
                     found in files")


    (options, args) = parser.parse_args()
    #determine user input
    if not (options.search) or not (options.replace):
        parser.error("must specifiy search and replace flags")
    #if options.verbose:
    #    print "reading %s..." % options.filename
    print "replace %s with %s in uc files" % \
        (options.search, options.replace)

    searchpath = os.getcwd()
    pattern = "*.uc"
    if options.filename:
        pattern = options.filename
        print "searching specific file: %s" % options.filename
    if options.pattern: pattern = options.pattern
    if options.directory: searchpath = options.directory
    mychangelist = None
    if options.changelist: mychangelist = options.changelist
    #start doing stuff
    #create default changelist
    matchingFiles = FindSearchMatches(searchpath, pattern, options.search)
    
    for filematch in matchingFiles:
        print filematch

    if matchingFiles:
        description = "massSearchAndReplaceUC automated changelist"
        
        if not mychangelist:
            mychangelist = CreateNewChangeList (description)

        for match in matchingFiles:
            P4EditFile(match,mychangelist)
            ReplaceInFile(match, options.search, options.replace)




if __name__ == "__main__":
    main()


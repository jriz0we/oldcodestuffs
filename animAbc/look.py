#!/usr/bin/env python2

# Copyright (c) 2012 Lucasfilm Ltd. All rights reserved. Used under
# authorization. This material contains the confidential and proprietary
# information of Lucasfilm Ltd. and may not be copied in whole or in part
# without the express written permission of Lucasfilm Ltd. This copyright
# notice does not imply publication.

import os,hashlib,random,string
import shutil
import maya.cmds as cmds

def cleanNamespace(pNamespace):
    cmds.namespace(set = ":")
    cmds.namespace(moveNamespace = [pNamespace, ":"], force = True)
    cmds.namespace(removeNamespace = pNamespace)

def _remove_namespace_from_dag_path(path):
    '''Returns the provided dag path with the namespace removed'''
    dagParts = path.split('|')
    dagParts = [part.split(':')[-1] for part in dagParts]
    scrubbedDag = '|'.join(dagParts)
    return scrubbedDag
def _dag_path_for_instance(dagPath, nameSpace):
    '''given a maya dag path, returns the node on an instance for it'''
    dagParts = dagPath.split('|')
    dagParts = [nameSpace+':'+part for part in dagParts]
    return '|'.join(dagParts)


#########################export job########################


def determineShaderList(exportJob):
    """docstring for determineSGContent"""
    sgObjectList = []
    sgNodeList = set()
    geomList = [obj['dagpath'] for obj in exportJob.geomObjectList]
    for geo in geomList:
        sgSetList = cmds.listSets(object = geo, t = 1, ets = True)
        if sgSetList == None: continue 
        sgList = [sg for sg in sgSetList if cmds.nodeType(sg) == 'shadingEngine']
        sgNodeList.update(sgList)
    if len(sgNodeList) == 1 and 'initialShadingGroup' in sgNodeList: return None
    #remove namespaces from the shader nodes to make a list of names
    sgNameList = list(sgNodeList)
    if exportJob.jobOptions['stripNamespaces']:
        sgNameList = [_remove_namespace_from_dag_path(shader) for shader in list(sgNodeList)]

    hashList = [addHashToShader(sg) for sg in list(sgNodeList)]
    #unwind all the lists into a dict, then make a list of dict objects
    for i in xrange(len(sgNodeList)):
        sgObject = {}
        sgObject['dagpath'] = list(sgNodeList)[i]
        sgObject['hash'] = hashList[i]
        sgObject['name'] = sgNameList[i]
        sgObject['index'] = i
        sgObjectList.append(sgObject)
    #return list(sgNodeList), sgNameList, hashList
    return sgObjectList

def addHashToShader(shaderNode):
    """docstring for addHashToShader"""
    if not cmds.attributeQuery( 'SG_hash', node= shaderNode, ex=True ):
        cmds.lockNode(shaderNode, l=False)
        cmds.addAttr(shaderNode, shortName='SG_hash', dataType='string')
    tHash = hashlib.md5()
    hashString = _remove_namespace_from_dag_path(shaderNode)
    #@TODO need to extend this hash some how
    tHash.update(str(hashString))
    cmds.setAttr(shaderNode+'.SG_hash', tHash.hexdigest(), type = 'string')
    return tHash.hexdigest()

def getLookRelationDict(exportJob):
    """docstring for getLookRelationDict"""
    lookRelationDict = {}
    geomList = [obj['dagpath'] for obj in exportJob.geomObjectList]
    for i in range(len(exportJob.sgObjectList)):
        filteredList = []
        faceMappedList = []
        #the actual node
        sg = exportJob.sgObjectList[i]
        #sgName = exportJob.sgNameList[i]
        if not lookRelationDict.has_key(sg['hash']):
            lookRelationDict[sg['hash']] = []
        assignmentList = cmds.sets(sg['dagpath'], query = True)
        assignmentList = cmds.ls(assignmentList, l = True)
        #filter out faceMapping assignments
        faceMappedList = [name for name in assignmentList if '.f' in name]
        #filter out assignments not in the export geom list
        filteredList = [name for name in assignmentList if name in geomList]
        #strip namesspaces - why?
        #filteredList = [ _remove_namespace_from_dag_path(p) for p in filteredList]
        faceMappedList.extend(filteredList)
        assignmentList = faceMappedList
        #make sure assignment list per hash = unique
        superSet = set(lookRelationDict[sg['hash']])
        superSet.update(assignmentList)
        lookRelationDict[sg['hash']] = list(superSet)

    return lookRelationDict

def getHashFromFaceMap(faceMap, exportJob):
    """docstring for getHashFromFaceMap"""
    geoName = faceMap.split('.f')[0]
    faceList = faceMap.split('.f')[-1]
    #has namespaces use full dagpath
    index = get_index(exportJob.geomObjectList, "dagpath", geoName)
    return index, faceList


def get_index(seq, attr, value):
    for each in seq:
        if each[attr] == value: 
            return each['index']

def updateLookMapFile(exportJob, lookRelationDict, mapFile):
    #@TODO maybe change the lookMapFile format if stripnames on or off???
    """docstring for writeLookMapFile"""
    # Start Writing files
    mapFile.write("ABC look map version 1.0\n")
    #Shader list block, includes namespaces in name
    mapFile.write("shader\n")
    mapFile.write("{\n")
    for i in range(len(exportJob.sgObjectList)):
        sg = exportJob.sgObjectList[i]
        hr = sg['dagpath']
        if exportJob.jobOptions['stripNamespaces']: hr = sg['name']
        mapFile.write("%i %s %s\n" % (i, hr, sg['hash']))
    mapFile.write("}\n")
    mapFile.write("\n")
    #geom list 
    mapFile.write("geo\n")
    mapFile.write("{\n")
    for i in range(len(exportJob.geomObjectList)):
        geo = exportJob.geomObjectList[i]
        hr = geo['dagpath']
        if exportJob.jobOptions['stripNamespaces']:hr = geo['name']
        mapFile.write("%i %s %s\n" % (i, hr, geo['hash']))
    mapFile.write("}\n")
    mapFile.write("\n")
    #mapping with facemapping support
    #column 1 is shader index, column to is geo index, or a facemapping group
    mapFile.write("mapping\n")
    mapFile.write("{\n")
    for sgHash, assigneeList in lookRelationDict.items():
        #shaderIndex = shaderNameList.index(sgName)
        sgIndex = get_index(exportJob.sgObjectList, 'hash',sgHash)
        for assignee in assigneeList:
            if '.f[' in assignee:
                geoIndex, faceList = getHashFromFaceMap(assignee, exportJob)
                #facemapped 
                mapFile.write("%i %s %s\n" % (sgIndex, geoIndex, faceList))
            else:
                geoIndex = get_index(exportJob.geomObjectList,'dagpath',assignee)
                mapFile.write("%i %s\n" % (sgIndex, geoIndex)) 
            

    mapFile.write("}\n")
    mapFile.close()

def writeLookMapFile(exportJob):
    """docstring for writeLookMapFile"""
    lookRelationDict = getLookRelationDict(exportJob)
    baseName = "%s.LOOKMAP.txt" % (exportJob.assetName)
    mapFilePath = os.path.join(exportJob.jobOptions['exportJobPath'], baseName)
    mapFile = open(mapFilePath, "w")
    updateLookMapFile(exportJob,lookRelationDict, mapFile)
    mapFile.close()
    print 'wrote lookMap:',mapFilePath
    return mapFilePath

def exportShaderCacheFile(exportJob):
    """docstring for exportShaderCacheFile"""
    #select the shaders only
    sgNodeList = [obj['dagpath'] for obj in exportJob.sgObjectList]
    print sgNodeList
    cmds.select(sgNodeList, noExpand = True)
    #determine where to save
    baseName = "%s.LOOK.ma" % (exportJob.assetName)
    lookCachePath = os.path.join(exportJob.jobOptions['exportJobPath'], baseName)
    #save file, export selected
    cmds.file(lookCachePath, es = True, type = "mayaAscii", force = True)
    print 'exported maya look cache:',lookCachePath
    return lookCachePath
        

def generateABCLookmapDict(exportJob):
    """docstring for generateABCLookmapDict """
    lookMapFile = exportJob.lookMapPath
    lookMapDict = {}
    fileInput = open(lookMapFile, "r")
    for line in fileInput:
        token = line.rstrip("\n")
        if token == "shader":
            lookMapDict["shader"] = processShaderTokens(fileInput)
        elif token == "geo":
            lookMapDict["geo"] = processGeoTokens(fileInput)
        elif token == "mapping":
            lookMapDict["mapping"] = processMappingTokens(fileInput)
            
    return lookMapDict

def findTexturePaths(lookCachePath):
    """return a list of textures paths from the maya file lookCachePath"""
    texturePaths = []
    print 'lookCachePath:',lookCachePath
    s = open(lookCachePath,'r')
    for line in s:
        if '$LIBRARY_ROOT' in line:
            #print line
            ll = line.split()
            tPath = ll.pop()
            tPath = tPath.replace('"','')
            tPath = tPath.replace(';','')
            #print tPath
            texturePaths.append(tPath)
            
    return texturePaths

def replaceTexturePath(line, newTexturePaths):
    """if line has a path in newtexturePaths, return line with path changed"""
    newLine = ""
    if '$LIBRARY_ROOT'in line:
        #hack this line since it has a reference node
        lineList = line.split()
        libPath = lineList[-1].split('"')[1]
        matched = [pathTuple for pathTuple in newTexturePaths if pathTuple[0] == libPath]
        if matched:
            #add formating for maya ascii format
            newPath = matched[0]
            newLine = line.replace(libPath,newPath[1])
    else:
        #otherwise copy line as is
        newLine = line
    return newLine


def updateLookCacheToLocalTextures(lookCachePath, texturePaths):
    print "updating LOOK file:", lookCachePath
    tempLook = lookCachePath.replace('.LOOK.ma','.LOOK.tmp.ma')
    s = open(lookCachePath,'r')
    n = open(tempLook, 'w')
    for line in s:
        #update the texture path line if needed
        updatedLine = replaceTexturePath(line,texturePaths)
        n.write(updatedLine)
    s.close()
    n.close()
    #replace updated lookCache
    shutil.move(tempLook, lookCachePath) 
    return 
 
def copyTexturesLocal(exportJob):
    """find the file texture paths in the animAbc look file,
    and copy them into a texture folder in the animAbc folder
    for that asset"""
    #setup the directory
    texLibDir = os.path.join(exportJob.jobOptions['exportJobPath'],'textures')
    if not os.path.exists(texLibDir):os.makedirs(texLibDir)
    #find the textures in the lookCache
    texturesInCache = findTexturePaths(exportJob.jobOptions['mayaLookCachePath'])
    #copy the textures to the cache texture lib
    tPathTuples = []
    texturesInCache = texturesInCache
    for texpath in texturesInCache:
        #print texpath
        realPath = os.path.expandvars(texpath)
        newPath = os.path.join(texLibDir,os.path.basename(realPath))
        if os.path.exists(realPath) and os.path.isfile(realPath):
            shutil.copy(realPath, newPath) 
            print 'copy:', realPath, '\nto:', newPath
            os.chmod(newPath, 0777)
            tPathTuples.append((texpath,newPath))
    #udpate the lookCache with paths to the local textures instead of the original paths
    updateLookCacheToLocalTextures(exportJob.jobOptions['mayaLookCachePath'],tPathTuples)

   
########################import section#############################       
def processShaderTokens(pFileInput):
    pFileInput.next() #skip the first one because its "{"
    token = pFileInput.next().rstrip("\n")
    shaderList = []
    while token != "}":
        shaderhash = token.split()[-1]
        shaderList.append(shaderhash)
        token = pFileInput.next().rstrip("\n")
            
    return shaderList

def processGeoTokens(pFileInput):
    pFileInput.next() #skip the first one because its "{"
    token = pFileInput.next().rstrip("\n")
    geoList = []
    while token != "}":
        geohash = token.split()[-1]
        geoList.append(geohash)
        token = pFileInput.next().rstrip("\n")
            
    return geoList

def processMappingTokens(pFileInput):
    pFileInput.next() #skip the first one because its "{"
    token = pFileInput.next().rstrip("\n")
    tMappingDict = {}
    while token != "}":
        tokenList = token.split()
        tShaderIndex = tokenList[0]
        tGeoIndex = tokenList[1]
        if len(tokenList) > 2: 
            faceList = tokenList[2]
            tGeoIndex +='.f'+ faceList
        if not tMappingDict.has_key(tShaderIndex):
            tMappingDict[tShaderIndex] = []
        tMappingDict[tShaderIndex].append(tGeoIndex)
        token = pFileInput.next().rstrip("\n")
    return tMappingDict


def findImportedGeomNodeByHash(importJob,geomHash):
    """docstring for findImportedGeomNodeByHash"""
    geomNode = None
    importedShapes = cmds.listRelatives(importJob.jobInfoNode, ad = True, f = True,
            type = ['mesh', 'nurbsSurface'])
    
    #print 'looking for hash',geomHash,'under', importJob.jobInfoNode
    for shape in importedShapes:
        hash = cmds.getAttr(shape+'.ABC_hash')
        if hash == geomHash:
            #@TODO find out if this is best way to get parent path
            geomNode = cmds.listRelatives(shape, p = True, f = True)[0]
            #print 'found match', geomNode
            break
    
    return geomNode
    
def findSgNodeInSceneBySG_hash(sgHash):
    sgNode = None
    allSgsInScene = cmds.ls(et = 'shadingEngine')
    #print 'looking for sg with hash',sgHash
    for sg in allSgsInScene:
        if cmds.attributeQuery('SG_hash', node = sg, ex = True):
            if sgHash == cmds.getAttr(sg + '.SG_hash'):
                sgNode = sg
                #print 'found match', sgNode
                break
    return sgNode
   
def findSgInSceneByName(sgName):
    sgInScn = False
    allSgsInScene = cmds.ls(et = 'shadingEngine')
    for sg in allSgsInScene:
        if ':' in sg: tempsg = sg.split(':')[1]
        else: tempsg = sg
        if sgName in tempsg:
            #print 'match',sgName,'to', sg
            sgInScn = True
            break
    return sgInScn 

def assignShaderToGeo(shaderName, geomName):
    """docstring for assignShaderToGeo"""
    #assign the shader to the geometry
    try:
        #print 'attempting to assign', geomName,'to', shaderName
        cmds.sets(geomName, edit = True, forceElement = (shaderName))
    except:
        print geomName, 'was supposed to get', shaderName, 'but something broke'


def doABCLookAssign(importJob):
    if not importJob.hasImported:importJob.doImportJob()
    #shader file
    shaderFile = importJob.mayaLookCachePath
    #Read Look Map
    tLookMapDict= generateABCLookmapDict(importJob)
    toImportSgHashList = tLookMapDict["shader"]
    toImportGeoHashList = tLookMapDict["geo"]
    mappingDict = tLookMapDict["mapping"]
    
    ############
    #Check if materials are already in scene
    tNeedImport = False
    #print'check for existing shaders in scene' 
    for hash in toImportSgHashList:
        if not findSgNodeInSceneBySG_hash(hash):
            print 'no match in scene'
            tNeedImport = True
            break
   
    ############# 
    #Import Shader File if it is not in Scene


    char_set = string.ascii_uppercase + string.digits
    tNamespace = 'ABCLookAssign' + ''.join(random.sample(char_set, 6))

    if tNeedImport:
        print 'importing shaders from', importJob.mayaLookCachePath
        cmds.file(shaderFile, i = True, namespace = tNamespace)
    else:
        tNamespace = ""

    #Find shader and geom names
    for shaderIndex, geoIndexList in mappingDict.items():
        for i in geoIndexList:
            faceList = ''
            geomName = None
            index = i
            sgHash = toImportSgHashList[int(shaderIndex)]
            shaderName = findSgNodeInSceneBySG_hash(sgHash)
            if ':' in shaderName:
                tNamespace = shaderName.split(':')[0]
            #print sgHash,shaderName
            #if facemapped
            if '.f[' in i:
                #print 'face mapped geo!!!!', i
                index = i.split('.f')[0]
                faceList = '.f'+i.split('.f')[-1]

            try:
                #print 'geoIndex:', i
                geomHash = toImportGeoHashList[int(index)]
                #print 'geomHash:', geomHash
                geomName = findImportedGeomNodeByHash(importJob,geomHash)
            except:
                raise StandardError("Failed to find content of mapping for %s %s " % (shaderIndex, i))
            #add faceList if available            
            geomName = geomName+faceList
            assignShaderToGeo(shaderName,geomName)

    #clean up the namespaces if the shader had to be imported
    if tNeedImport:
        print 'removing namespace',tNamespace
        cleanNamespace(tNamespace)

   

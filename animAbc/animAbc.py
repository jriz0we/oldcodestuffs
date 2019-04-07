#!/usr/bin/env python2

# Copyright (c) 2012 Lucasfilm Ltd. All rights reserved. Used under
# authorization. This material contains the confidential and proprietary
# information of Lucasfilm Ltd. and may not be copied in whole or in part
# without the express written permission of Lucasfilm Ltd. This copyright
# notice does not imply publication.

import os  
import maya.cmds as cmds
import maya.mel as mel

import geom 
import look
import ui

class exportJob(object):
    def __init__(self,topNode):
        object.__init__(self)
        self.topNode = topNode
        #drop a namespace if it exists
        self.assetName = topNode.split(':')[-1].split('|')[-1]
        self.getRefNodes()

    def getRefNodes(self):
        """find all refNodes associated with this exportJob"""
        #find out if selection is referenced into scene
        #loop through children of top node, if referened, find refNode adding it to list
        children = cmds.listRelatives(self.topNode, ad = True, f = True)
        refChildren = [kid for kid in children if cmds.referenceQuery(kid, inr = True)]
        refNodes = []
        for refChild in refChildren:
            if cmds.referenceQuery(refChild, rfn = True, tr = True) in refNodes:
                continue
            refNodes.append(cmds.referenceQuery(refChild, rfn = True, tr = True))
        #@TODO Fix this
        refNodeString = ''
        for ref in refNodes: refNodeString = refNodeString+ref+';'
        return refNodeString

    def getBaseCachePath(self):
        """docstring for getBaseCachePath"""
        #FOR LAL/ILM shows
        if os.environ.get('TASK_PATH') or os.environ.get('SHOTDIR'):
            basePath = os.path.join(os.environ['TASK_PATH'], "animAbc",self.assetName)
            if not os.path.exists(basePath):os.makedirs(basePath)
        #just use the project settings
        else:
            currProjPath = cmds.workspace(q = True, rd = True)
            basePath = os.path.join(currProjPath,"animAbc",self.assetName)
            if not os.path.exists(basePath): os.makedirs(basePath)
        return basePath

    def getExportJobPath(self):
        """docstring for mkAssetCacheDir"""
        #stripNameSpace and fullPath if passed
        from datetime import datetime
        dt_obj = datetime.now()
        date_str = dt_obj.strftime("%Y%m%d_%H%M%S")
        uniqueDir = self.assetName+ '_'+date_str
        exportJobDir = os.path.join(self.jobOptions['baseCachePath'],uniqueDir)
        if not os.path.exists(exportJobDir): os.makedirs(exportJobDir)
        return exportJobDir

    def getABCCachePath(self):
        """docstring for getAssetFilePath"""
        baseName = "%s.abc" % (self.assetName)
        dirName = self.jobOptions['exportJobPath']
        return os.path.join(dirName,baseName)


    # exportJob tracking transform
    def createExportJobInfo(self):
        """docstring for createExportJobInfo"""
        #create attributes for cache data
        self.jobInfoNode = cmds.createNode('transform', n = self.assetName+'_ABC')
        cmds.addAttr(self.jobInfoNode, shortName='AlembicCachePath', dataType='string')
        cmds.addAttr(self.jobInfoNode, shortName='MayaLookCachePath', dataType='string')
        cmds.addAttr(self.jobInfoNode, shortName='LookMapPath', dataType='string')
        cmds.addAttr(self.jobInfoNode, shortName='SelectedPath', dataType = 'string')
        cmds.addAttr(self.jobInfoNode, shortName='ReferenceNode', dataType = 'string')

    def updateExportJobInfo(self):
        """docstring for updateExportJobInfo"""
        #update attributes for cache data
        cmds.setAttr(self.jobInfoNode+'.AlembicCachePath', self.jobOptions['ABCCachePath'], type = 'string')
        cmds.setAttr(self.jobInfoNode+'.SelectedPath', self.topNode, type = 'string')
        if self.jobOptions.has_key('mayaLookCachePath'):
            cmds.setAttr(self.jobInfoNode+'.MayaLookCachePath', self.jobOptions['mayaLookCachePath'], type = 'string')
        if self.jobOptions.has_key('lookMapPath'):
            cmds.setAttr(self.jobInfoNode+'.LookMapPath', self.jobOptions['lookMapPath'], type = 'string')
        if self.jobOptions.has_key('refNodes'):
            cmds.setAttr(self.jobInfoNode+'.ReferenceNode',self.jobOptions['refNodes'], type = 'string')

    def getDefaultExportJobOptions(self, exportJobOptions = None):
        """docstring for getDefaultExportJobOptions"""
        self.jobOptions = {}
        self.jobOptions['startFrame'] = str(cmds.playbackOptions( query = True, minTime = True ))
        self.jobOptions['endFrame'] = str(cmds.playbackOptions( query = True, maxTime = True ))
        self.jobOptions['timeStep'] = '1'
        #@TODO put in support for frameRelativeSample List
        self.jobOptions['baseCachePath'] = self.getBaseCachePath()
        self.jobOptions['attrList'] = ['assetName','assetVersion','productionAsset','assetClass','assetId']
        self.jobOptions['attrPrefixList'] = []
        self.jobOptions['userPropList'] = []
        self.jobOptions['userPrefixList'] = []
        self.jobOptions['copyLookLocal'] = False
        #option human readable : flag
        self.optionMapping = {'uvWrite':'-uv','noNormals':'-nn',
                'writeVisbility':'-wv', 'stripNamespaces':'-sn', 'renderOnly':'-ro',
                'writeColorSets':'-wcs', 'wholeFrameGeo':'-wfg', 'worldSpace':'-ws'
                }
        #set tool defaults
        defaultsOpts = ['verbose','selection','uvWrite','noNormals','stripNamespaces']
        for opt in defaultsOpts:
            self.jobOptions[opt] = True
        if exportJobOptions:
            print 'updating defaults with overrides'
            self.jobOptions.update(exportJobOptions)
        #if the udpated changed baseCachePath, update exportJobPath() 
        self.jobOptions['exportJobPath'] = self.getExportJobPath()
        #get the refNodes associated with exportJob
        self.jobOptions['refNodes'] = self.getRefNodes()

    # running the exportJob
    def buildAlembicExportCommand(self):
        """docstring for buildAlembicExportCommand"""

        #jobstring argument list
        jobStringArgs = ['-fr',str(self.jobOptions['startFrame']),str(self.jobOptions['endFrame']),
                    '-s',str(self.jobOptions['timeStep'])]
                            
        for key, opt in self.optionMapping.items():
            #if flag is in the main dictionary as True, append the flag to the string
            if self.jobOptions.has_key(key) and self.jobOptions[key]:
                jobStringArgs.append(opt)

        #attribute strings defaults for CW
        attrString = ''
        for attr in [a for a in self.jobOptions['attrList'] if a != '']: attrString += ' -a '+attr
        for prefix in [a for a in self.jobOptions['attrPrefixList'] if a != ''] :attrString += ' -atp '+prefix
        #user property attribute list
        userPropString = ''
   
        for attr in [a for a in self.jobOptions['userPropList'] if a != '']: userPropString += ' -u '+ attr
        for prefix in [a for a in self.jobOptions['userPrefixList'] if a != '']: userPropString += ' -uatp '+ prefix
        
        #process self.jobOptions['exportFilePath']
        #always use the selection option, till we can use root
        jobStringArgs.extend(['-sl', '-file',self.jobOptions['ABCCachePath']])

        #combine command string
        melCmd = 'AbcExport -j "ARGS"'
        if self.jobOptions['verbose']: melCmd = melCmd.replace('-j','-v -j')
        jobString = ' '.join(jobStringArgs)
        jobString += attrString
        self.exportCmd = melCmd.replace('ARGS',jobString)

    def runAlembicExportCommand(self):
        """docstring for runAlembicExportCommand"""
        #@TODO figure out how to optimize multiple jobs with 1 evaluation
        #can't do this till I can not rely on -sl
        print self.exportCmd
        mel.eval(self.exportCmd)
        print 'done, cache:',self.jobOptions['ABCCachePath']


    def doExportJob(self,exportJobOptions = None):
        """docstring for doExportJob"""
        print 'starting cache export for', self.topNode
        #paths to export to
        self.getDefaultExportJobOptions(exportJobOptions)
        #create the exportJobInfo 
        self.createExportJobInfo()
        
        #get geom paths and names
        self.geomObjectList = geom.determineExportGeomFromTopNode(self)
        #get shader paths and names
        self.sgObjectList = look.determineShaderList(self)
        #if shaders, proceed to cache look
        if self.sgObjectList != None:
            #write the lookMap 
            self.jobOptions['lookMapPath'] = look.writeLookMapFile(self)
            #export shaders 
            self.jobOptions['mayaLookCachePath'] = look.exportShaderCacheFile(self)
         
        self.jobOptions['ABCCachePath'] = self.getABCCachePath()
        self.updateExportJobInfo() 
        #export the abc geometery cache
        #select the geometry 
        cmds.select([obj['dagpath'] for obj in self.geomObjectList])
        #build the export command
        self.buildAlembicExportCommand()
        
        #this needs to be last till I can get it to 'let go'
        self.runAlembicExportCommand()
        if self.jobOptions['copyLookLocal']:
            print 'copy local turned on'
            look.copyTexturesLocal(self)
        cmds.select(clear = True) 

#end exportJob class
class importJob(object):
    def __init__(self,cacheInfoNode):
        """docstring for __init__"""
        self.jobInfoNode = cacheInfoNode
        self.hasImported = self.getImports()
        self.getPaths()

    def getPaths(self):
        """docstring for getPaths"""
        try:
            self.abcCachePath = cmds.getAttr(self.jobInfoNode+'.AlembicCachePath')
            self.mayaLookCachePath = cmds.getAttr(self.jobInfoNode+'.MayaLookCachePath')
            self.lookMapPath = cmds.getAttr(self.jobInfoNode+'.LookMapPath')
        except:
            print '%s does not have the attributes required to be an animAbc import transform'% self.jobInfoNode
        if cmds.attributeQuery('SelectedPath',node = self.jobInfoNode, ex = True):
            self.selectNode = cmds.getAttr(self.jobInfoNode+'.SelectedPath')
        if cmds.attributeQuery('ReferenceNode', node = self.jobInfoNode, ex = True):
            self.refNode = cmds.getAttr(self.jobInfoNode+'.ReferenceNode')

    def getImports(self):
        """docstring for getImports"""
        hasImported = False
        if cmds.listRelatives(self.jobInfoNode, c = True):
            hasImported = True
        return hasImported

    def unloadCacheSrc(self):
        """docstring for unloadCacheSrc"""
        #if the string isnt empty, split into list of RN nodes
        if self.refNode != '':
            refNodes = self.refNode.split(';')
        #unload each RN
        for ref in refNodes:
            if cmds.objExists(ref) and cmds.referenceQuery(ref, il = True): 
                cmds.file(unloadReference = ref)
    
    def runAlembicImportCommand(self):
        """docstring for runAlembicImportCommand"""
        if self.hasImported:
            print "%s already has children cancelling import" % self.jobInfoNode
            return
        print self.importCmd
        mel.eval(self.importCmd)
        print 'done with import for:',self.jobInfoNode
        return

    def buildAlembicImportCommand(self):
        """docstring for buildAlembicImportCommand"""
        jobStringArgs = ['-d','-sts',
                '-rpr','"'+self.jobInfoNode+'"',
                '-mode','import','"'+self.abcCachePath+'"']

        #combine command string
        melCmd = 'AbcImport ARGS'
        jobString = ' '.join(jobStringArgs)
        self.importCmd = melCmd.replace('ARGS',jobString)   
    
    def doImportJob(self):
        """docstring for doImportJob"""
        if self.abcCachePath == '': 
            print "%s doesn't have a valid Alembic Cache Path" % self.jobInfoNode
            return
        self.buildAlembicImportCommand()
        self.runAlembicImportCommand()

        #@TODO put back in unload references 
        #self.unloadCacheSrc()

    def doLookAssignShaders(self):
        """docstring for doLookAssignShaders"""
        if not self.mayaLookCachePath: 
            print "%s doesnt have a valid Maya Look Cache Path" % self.jobInfoNode
            return
        elif not self.lookMapPath:
            print "%s doesnt have a valid Look Map Path" % self.jobInfoNode
            return
        look.doABCLookAssign(self)
#end of importJob class

#animAbc procedures

def loadAbcImportPlugin():
    '''
    load the AbcImport plugin if not loaded
    '''
    if not cmds.pluginInfo('AbcImport', q = True, l = True):
        cmds.loadPlugin('AbcImport')
    return
def loadAbcExportPlugin():
        '''
        load the AbcExport plugin if not loaded
        '''
        if not cmds.pluginInfo('AbcExport', q = True, l = True):
            cmds.loadPlugin('AbcExport')
        return
def exportAndImport(exportJobOptions = None):
    """docstring for exportAndImport"""
    cacheSelectedContent(exportJobOptions)
    importAndAssignShaders()

def cacheSelectedContent(exportJobOptions = None):
    """docstring for cacheSelectedContent"""
    jobsList = []
    #build the list of selected content
    for asset in cmds.ls(sl = True, l = True):
        jobsList.append(exportJob(asset))
    #loop through the exports, this is inefficent 
    #but is based on the selection based method
    for job in jobsList:
        job.doExportJob(exportJobOptions)
    #select the created importJob transforms
    for job in jobsList:
        cmds.select(job.jobInfoNode, add = True)
    return True

def importSelectedContent(*args):
    """docstring for importSelectedContent"""
    jobList = []
    #build the a list of import jobs to execute
    for jobNode in cmds.ls(sl = True, l = True):
        jobList.append(importJob(jobNode))
    #do imports
    #@TODO make more robust if the the import job already has contents imported
    for job in jobList:
        job.doImportJob()

def importAndAssignShaders(*args):
    """docstring for importAndAssignShaders"""
    jobList = []
    #make the list of import job transforms
    for jobNode in cmds.ls(sl = True, l = True):
        jobList.append(importJob(jobNode))
    #assign looks if they exist for each importJob transform
    for job in jobList:
        job.doLookAssignShaders()

def openExportUI(exportJobOptions = None):
    """docstring for openExportUI"""
    ui.openExportUI(exportJobOptions)

def openAnimAbcUI():
    """docstring for openAnimAbcUI"""
    ui.openAnimAbcUI()

def unloadSrc():
    jobList = []
    #make the list of import job transforms
    for jobNode in cmds.ls(sl = True, l = True):
        jobList.append(importJob(jobNode))
    #assign looks if they exist for each importJob transform
    for job in jobList:
        job.unloadCacheSrc()



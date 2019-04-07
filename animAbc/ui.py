#!/usr/bin/env python2_maya

# Copyright (c) 2012 Lucasfilm Ltd. All rights reserved. Used under
# authorization. This material contains the confidential and proprietary
# information of Lucasfilm Ltd. and may not be copied in whole or in part
# without the express written permission of Lucasfilm Ltd. This copyright
# notice does not imply publication.

import maya.cmds as cmds
import animAbc

class ExportUI():
    '''common init for ui'''
    
    def __init__(self,Title, exportJobOptions = None):
        self.title = Title 
        self.uiName = self.title.strip(' ')
        self.bttnHght = 40
        self.bttnWdth = 200 
        self.wndwWidth = self.bttnWdth * 2.25 +15
        self.wndwHght = 1000
        self.emptyString = ''
        self.getDefaultExportSettings( exportJobOptions)
    
    def getDefaultExportSettings(self, exportJobOptions):
        """docstring for getDefaultSettings"""
        self.jobOptions = {}
        self.jobOptions['startFrame'] = cmds.playbackOptions( query = True, minTime = True )
        self.jobOptions['endFrame'] = cmds.playbackOptions( query = True, maxTime = True )
        self.jobOptions['timeStep'] = '1'
        #@TODO put in support for frameRelativeSample List
        #default attrs for CW
        self.jobOptions['attrList'] = ['assetName','assetVersion','productionAsset','assetClass','assetId']
        self.jobOptions['attrPrefixList'] = []
        self.jobOptions['userPropList'] = []
        self.jobOptions['userPrefixList'] = []
        self.jobOptions['copyLookLocal'] = False
        #option : flag
        self.optionMapping = {'uvWrite':'-uv','noNormals':'-nn',
                'writeVisibility':'-wv', 'stripNamespaces':'-sn', 'renderOnly':'-ro',
                'writeColorSets':'-wcs', 'wholeFrameGeo':'-wfg', 'worldSpace':'-ws',
                'verbose':'-v'
                }
        #set tool defaults
        defaultsOpts = ['verbose','selection','uvWrite','noNormals','stripNamespaces']
        for opt, flag in self.optionMapping.items():
            #create the key with default to off
            self.jobOptions[opt] = False
            #turn on the defaults if not overridden
            if opt in defaultsOpts: self.jobOptions[opt] = True
        #if there are overrides, update
        if exportJobOptions:
            print 'updating jobOptions'
            self.jobOptions.update(exportJobOptions)
        
    def queryUIForExportSettings(self,*args):
        '''
        use the ui update an dictionary object to pass on to animAbc 
        '''
        #query the ui
        expDict = {}
        widgetsToCheck = {'verbose':'verboseCheck',
                'uvWrite':'uvWriteCheck',
                'noNormals':'noNormalsCheck',
                'stripNamespaces':'stripNamespacesCheck',
                'renderOnly':'renderOnlyCheck',
                'writeVisibility':'writeVisibilityCheck',
                'worldSpace':'worldSpaceCheck',
                'wholeFrameGeo':'wholeFrameGeoCheck',
                'attrList':'attrListTextField',
                'attrPrefixList':'attrPrefixListTextField',
                'userPropList':'userPropListTextField',
                'userPrefixList':'userPrefixListTextField',
                'copyLookLocal':'copyLookLocalCheck'
                }
        #time range flags
        expDict['startFrame'] = cmds.floatFieldGrp(self.widgets['frameRangeGrp'], 
                query = True, value1 = True)
        expDict['endFrame'] = cmds.floatFieldGrp(self.widgets['frameRangeGrp'],
                query = True, value2 = True)
        expDict['timeStep'] = cmds.floatFieldGrp(self.widgets['timeStepGrp'], 
                query = True, value1 = True)
        #checkboxs and text fields
        for option, widget in widgetsToCheck.items():
            if 'Check' in widget:
                expDict[option] = cmds.checkBox(self.widgets[widget],
                        query = True, value = True)
            if 'TextField' in widget:
                tempList= cmds.textField(self.widgets[widget], 
                        query = True, text = True).split(';')
                if tempList[0] != '': expDict[option] = tempList

        #file browser
        overridePath = cmds.textFieldButtonGrp(self.widgets['filePathGrp'], 
                query = True, text = True)
        if overridePath != '': expDict['baseCachePath'] = overridePath
        
        self.jobOptions.update(expDict)
        #print expDict
        animAbc.cacheSelectedContent(self.jobOptions)
        self.closeWindow()
        return
    
    def getCachePath(self):
        '''open a file browser dialog to get a file path'''
        filePathGrpText = cmds.textFieldButtonGrp(self.widgets['filePathGrp'], query = True, 
                text = True)

        self.fileDialogePath = cmds.fileDialog2(fileMode = 3,
                caption="Please select a directory for the caches to be created in",
                dialogStyle=2)
        if self.fileDialogePath:
            filePathGrpText = self.fileDialogePath[0]
        cmds.textFieldButtonGrp(self.widgets['filePathGrp'], edit = True, 
                text = filePathGrpText)
        cmds.showWindow(self.uiWindow)
        return self.fileDialogePath

    def create(self):
        '''docstring for create'''
        
        self.widgets = {}

        if cmds.window(self.uiName, exists = True):
            cmds.deleteUI(self.uiName)
        self.uiWindow = cmds.window(self.uiName, title = self.title)
        self.mainScroll = cmds.scrollLayout() 
        self.mainCol = cmds.columnLayout(adjustableColumn=True)
        self.timeOptFrame = cmds.frameLayout( l='Time Range Options',
                borderStyle='in' )
        self.widgets['frameRangeGrp'] = cmds.floatFieldGrp(nf = 2, l = 'Frame Range',
                value1 = self.jobOptions['startFrame'],
                value2 = self.jobOptions['endFrame'])
        self.widgets['timeStepGrp'] = cmds.floatFieldGrp(nf = 1, l = 'Time Step',
                value1 = float(self.jobOptions['timeStep']))

        #end of time range options
        cmds.setParent("..")
        self.exportOptFrame = cmds.frameLayout( l='Export Options', borderStyle='in')
        flagOptionMap = {'verbose':'-v','uvWrite':'-uv','noNormals':'-nn',
                'writeVisibility':'-wv', 'stripNamespaces':'-sn', 'renderOnly':'-ro',
                'writeColorSets':'-wcs', 'wholeFrameGeo':'-wfg', 'worldSpace':'-ws'
                }
        #create checkbox widget, default to off
        for option,flag in flagOptionMap.items():
            widgetName = option+'Check'
            #turn on defaults
            self.widgets[widgetName] = cmds.checkBox( l = '-%s / %s'% (option,flag),
                    enable = True, value = self.jobOptions[option])

        #end of export options
        cmds.setParent("..")
        self.advOptFrame = cmds.frameLayout( l='Adv. Options',
                borderStyle='in')
        #attribute exports
        
        defaultAttrString = ';'.join(self.jobOptions['attrList'])
        defaultAttrPrefixString= ';'.join(self.jobOptions['attrPrefixList'])
        defaultUserPropString = ';'.join(self.jobOptions['userPropList'])
        defaultUserPrefixString= ';'.join(self.jobOptions['userPrefixList'])
        self.attrFrame = cmds.frameLayout(
                l = 'Attribute Export: separate attrs with ";"', 
                borderStyle = 'in')
        self.widgets['attrListTextField']=cmds.textField(
                tx = defaultAttrString, enable = True)
        self.attrPrefixFrame = cmds.frameLayout(
                l = 'Attribute Prefix: separate prefixes with ";"', 
                borderStyle = 'in')
        self.widgets['attrPrefixListTextField'] = cmds.textField(
                tx = defaultAttrPrefixString, enable = True)
        #user property exports
        self.userFrame = cmds.frameLayout( 
                l = 'User Property Export: separate attrs with ";"', 
                borderStyle = 'in')
        self.widgets['userPropListTextField']=cmds.textField(
                tx = defaultUserPropString, enable = True)
        self.userPrefixFrame = cmds.frameLayout(
                l = 'User Prop user Prefix: separate prefixes with ";"', 
                borderStyle = 'in')
        self.widgets['userPrefixListTextField'] = cmds.textField(
                tx = defaultUserPrefixString, enable = True)
        cmds.setParent("..")
        self.widgets['copyLookLocalCheck'] = cmds.checkBox( l =' Copy texure paths to cache',
                enable = True, value = self.jobOptions['copyLookLocal'])


        #end of advanced options
        cmds.setParent("..")
        #cmds.setParent(self.mainCol)
        self.filePathFrame = cmds.frameLayout( l='Override Export Path', borderStyle='in' )

        self.widgets['filePathGrp'] = cmds.textFieldButtonGrp( l='File Path',
                ad3 = 2, cl3 = ['left','left','right'],
                #@TODO fix this after lunch
                text=self.emptyString,
                buttonLabel='Browse',
                bc = self.getCachePath,
                p = self.filePathFrame,
                width = self.bttnWdth *2.1)

        cmds.setParent("..")
        self.btnRowLayout = cmds.rowLayout(numberOfColumns = 2, 
                columnAttach=[(1, 'both', 0), (2, 'both', 0)])
        self.widgets['execButton'] = cmds.button(l = 'run Export command', h = self.bttnHght,
                w = self.bttnWdth,
                command = self.queryUIForExportSettings, 
                ann = 'Execute the export command from the UI ')
        self.widgets['closeButton'] = cmds.button( label='Cancel', h = self.bttnHght,
                w = self.bttnWdth,
                command=self.closeWindow,
                ann = 'Cancel Export UI ')

        cmds.showWindow(self.uiWindow)
        cmds.window(self.uiWindow, edit =True, width = self.wndwWidth)

    def closeWindow(self):
        cmds.windowPref(self.uiWindow, remove=True )
        cmds.deleteUI(self.uiWindow, window = True)

class animAbcUI():
    '''docstring for animAbcUI, this ui has buttons for the highlevel animAbc procedures'''

    def __init__(self,Title, exportJobOptions = None):
        self.title = Title 
        self.uiName = self.title.strip(' ')
        self.bttnHght = 40
        self.bttnWdth = 250 
        self.wndwWidth = self.bttnWdth * 1.05
        self.emptyString = ''

    def create(self):
        '''docstring for create'''
        
        self.widgets = {}

        if cmds.window(self.uiName, exists = True):
            cmds.deleteUI(self.uiName)
        self.uiWindow = cmds.window(self.uiName, title = self.title)
        self.mainScroll = cmds.scrollLayout() 
        self.mainCol = cmds.columnLayout(adjustableColumn=True)
        buttonProcList = [('AnimAbc Export (default)',animAbc.cacheSelectedContent),
                ('AnimAbc Export (options)',openExportUI),
                ('Import animAbc',animAbc.importSelectedContent),
                ('Import animAbcWithLook',animAbc.importAndAssignShaders),
                ('Export And Import (default)',animAbc.exportAndImport)]

        self.wndwHght = self.bttnHght * len(buttonProcList) + 10
        for button in buttonProcList:
            self.widgets[button[0]] = cmds.button(l = button[0], h = self.bttnHght,
                w = self.bttnWdth,
                c= button[1])


        cmds.showWindow(self.uiWindow)
        cmds.window(self.uiWindow, edit =True, width = self.wndwWidth, height = self.wndwHght)
    
   
def openExportUI(exportJobOptions = None):
    """docstring for openExportUI"""
    newWindow = ExportUI('animAbc Export UI beta',exportJobOptions)
    newWindow.create()


def openAnimAbcUI():
    """docstring for openExportUI"""
    newWindow = animAbcUI('animAbc UI')
    newWindow.create()


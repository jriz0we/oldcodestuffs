#!/usr/bin/env python2

# Copyright (c) 2010 Lucasfilm Ltd. All rights reserved. Used under
# authorization. This material contains the confidential and proprietary
# information of Lucasfilm Ltd. and may not be copied in whole or in part
# without the express written permission of Lucasfilm Ltd. This copyright
# notice does not imply publication.

import os, sys, format, random
import commands
import traceback
import maya.cmds as cmds
import maya.mel as mel
#hard coded example file
dressRig = '/show/cw/dev/art/jrowe/dressExample.ma'
'''dressUI is a class object, which helps with using maya's ui calls in python
this contains all the base functions I use in the example, they could be removed
from the ui'''
class dressUi():
    
    def importDressRigFile(self,*args):
        '''import a file with the geo to be instanced, a good idea would be to make 
        this work for different files for different episodes'''
        print ("importing dress kit geo\n");
        cmds.file(dressRig, i = True, type = 'mayaAscii')
        return
    
    def addDressToSelected(self,*args):
        '''adds the dress particle system to the selected geo(s)'''
        dressType = 'all'
        defaultCount = self.ptcCount
        uniSeed = random.randrange(1, 360,1)
        selected = cmds.ls(sl = True)
        for surface in selected:
            (emitSurface, emitter, emitSurfPtcs, emitSurfPtcsShape,insterName) = self.createParticleBucket(surface,dressType,defaultCount)
            self.updateParticleBucket(emitSurfPtcsShape)
            self.makeDyanmic(emitter,emitSurfPtcs)
            self.createInstancer(insterName,emitSurfPtcsShape)
        if not cmds.play( q=True, state=True ):cmds.play( forward=True )
        return    
    def getShadingGroupsFromShape(self,shapeNode):
        if cmds.objExists(shapeNode):
            destinations = cmds.listConnections(shapeNode, type = 'shadingEngine', d = True, s = False, p = False)
            return destinations[0]
            
    def getMaterialFromSG(self,shadingGroup):
        if 'shadingEngine' == cmds.nodeType(shadingGroup) and cmds.connectionInfo((shadingGroup+'.surfaceShader'),id = True):
            materialString = cmds.connectionInfo((shadingGroup+'.surfaceShader'), sfd = True)
            materialNode = materialString.split('.')
            return materialNode[0]
        
    def getTextureFromMaterial(self,material):
        classifications = cmds.getClassification(cmds.nodeType(material))
        if 'shader/surface' == classifications[0] and cmds.connectionInfo((material+'.color'),id = True):
            textureString = cmds.connectionInfo((material+'.color'), sfd = True)
            textureNode = textureString.split('.')
            return textureNode[0]
        
    def addShaderToSelected(self,*args):
        selected = cmds.ls(sl = True)
        for surf in selected:
            newMat = cmds.shadingNode('lambert', asShader=True, name = surf+'_instPaint1')
            newSG = cmds.sets(name = newMat+'SG', r = True, nss = True, em = True)
            texture = cmds.shadingNode('file', asTexture = True, name = surf+'_instPaintFile1')
            #cmds.connectAttr(texture+.'outColor' ,newMat+'.color', force = True )
            cmds.defaultNavigation(connectToExisting = True, source = texture, destination = newMat)
            cmds.defaultNavigation(connectToExisting = True, source = newMat, destination = newSG)
            cmds.select( clear=True )
            print "select",surf
            cmds.select(surf)
            print "assign",newMat,"to",surf
            cmds.hyperShade( newMat, assign=True )
            cmds.sets(edit= True,fe = newSG)
        
    def connectTextureToEmitter(self,*args):
        selected = cmds.ls(sl = True)
        for surf in selected:
            shapeNode = cmds.ls(surf, type = 'mesh', dag = True, ni = True)
            SG = self.getShadingGroupsFromShape(shapeNode[0])
            material = self.getMaterialFromSG(SG)
            fileNode = self.getTextureFromMaterial(material)
            cmds.connectAttr(fileNode+'.outColor',surf+'_Dress_Emitter.textureRate',force = True)
            cmds.setAttr(surf+'_Dress_Emitter.enableTextureRate', 1)
        
    def disconnectTextureFromEmitter(self,*args):
        selected = cmds.ls(sl = True)
        for surf in selected:
            shapeNode = cmds.ls(surf, type = 'mesh', dag = True, ni = True)
            SG = self.getShadingGroupsFromShape(shapeNode[0])
            material = self.getMaterialFromSG(SG)
            fileNode = self.getTextureFromMaterial(material)
            cmds.setAttr(surf+'_Dress_Emitter.enableTextureRate', 0)
            cmds.disconnectAttr(fileNode+'.outColor',surf+'_Dress_Emitter.textureRate')
    
    def createParticleBucket(self,emitSurface,dressType,ptcCount):
        '''creates a particle system named after the surface that the particles emit from
        returns the emitter, particles, instancer created.  This proc also builds
        the initial expressions that a modified by the UI'''
        firstFrame = cmds.playbackOptions( query = True, minTime = True )
        print ("creating a new particle for ")
        #TODO build a data class that is easily edited outside the script to set
        #these default settings
        if dressType == 'all':
            emitSurfaceName = emitSurface + "_Dress"
            scaleMin = str(self.ptcMin)
            scaleMax = str(self.ptcMax)
        emitterName = emitSurfaceName +"_Emitter"
        ptcBktName = emitSurfaceName + "_Particles"
        insterName = emitSurfaceName + "_Instancer"
        cmds.select(emitSurface)
        #create the emitter 
        emitter = cmds.emitter(type = 'surface', r=1000, nuv=True,spd = 0.01, sro = False, cye = 'none', cyi = 0, sp = 0, n = emitterName )
        #create the particles
        emitSurfPtcs = cmds.particle( c = 1.0, name = ptcBktName )
        cmds.goal(emitSurfPtcs, w=1,utr=0,g = emitSurface)
        emitSurfPtcsShape = emitSurfPtcs[-1]
        #add the per particle attributes
        cmds.select(emitSurfPtcsShape)
        #instance selection 
        cmds.addAttr( ln ='indexPP',dt = 'doubleArray')
        #random scaling
        cmds.addAttr( ln ='scalePP',dt = 'vectorArray') 
        #rotation vector around X axis based on surface normal
        cmds.addAttr( ln ='surfRotOffPP',dt = 'vectorArray')
        cmds.addAttr( ln ='surfRotPP',dt = 'vectorArray')
        #user specificied aim & user specified aim rotation around aim
        #not used in the example but can be leveraged for different behavior
        cmds.addAttr( ln ="aimVectorPP",dt = 'vectorArray')
        cmds.addAttr( ln ="aimRotOffPP",dt = 'vectorArray')
        cmds.addAttr( ln ="aimRotPP",dt = 'vectorArray')
        #Goal UV based attrs
        cmds.addAttr( ln ='goalWorldNormal0PP',dt = 'vectorArray')
        cmds.addAttr( ln ='goalU',dt = 'doubleArray')
        cmds.addAttr( ln ='goalU0',dt = 'doubleArray')
        cmds.addAttr( ln ='goalV',dt = 'doubleArray')
        cmds.addAttr( ln ='goalV0',dt = 'doubleArray')
        cmds.addAttr( ln ='parentU',dt = 'doubleArray')
        cmds.addAttr( ln ='parentU0',dt = 'doubleArray')
        cmds.addAttr( ln ='parentV',dt = 'doubleArray')
        cmds.addAttr( ln ='parentV0',dt = 'doubleArray')
        #custom attrs from the UI that change how the system behaves
        cmds.addAttr( ln = 'scaleMin', at ='double')
        cmds.addAttr( ln = 'scaleMax', at ='double')
        cmds.addAttr( ln = 'dressType', dt = 'string')
        cmds.addAttr( ln = 'randSeed', at = 'long')
        #update the attrs 
        cmds.setAttr(emitSurfPtcsShape+'.scaleMin', float(scaleMin))
        cmds.setAttr(emitSurfPtcsShape+'.scaleMax', float(scaleMax))
        cmds.setAttr(emitSurfPtcsShape+'.dressType', str(dressType), typ = 'string')
        cmds.setAttr(emitSurfPtcsShape+'.seed[0]', random.randrange(100, 360,1))
        cmds.setAttr(emitSurfPtcsShape+'.randSeed', random.randrange(100, 360,1))
        cmds.setAttr(emitSurfPtcsShape+".maxCount",int(ptcCount))
        cmds.setAttr(emitSurfPtcsShape+".startFrame", firstFrame)
        #return what was created
        return (emitSurface,emitter,emitSurfPtcs,emitSurfPtcsShape,insterName)
    
    def updateParticleBucket(self,emitSurfPtcsShape):
        '''update the settings of the particle system passed to the proc'''
        randSeed = cmds.getAttr(emitSurfPtcsShape+'.randSeed')
        scaleMin = cmds.getAttr(emitSurfPtcsShape+'.scaleMin')
        scaleMax = cmds.getAttr(emitSurfPtcsShape+'.scaleMax')
        dressType = cmds.getAttr(emitSurfPtcsShape+'.dressType')
        
        if dressType == 'all':
            instSize = str(len(cmds.listRelatives('dressExampleGrp', c = True, f = True)))
        #build the strings that set the on creation expression
        createExp = 'seed('+str(randSeed)+'+id);\ngoalU = parentU;\ngoalV = parentV;\n'
        createExp +=emitSurfPtcsShape+'.indexPP = floor(rand('+instSize+'));\n'
        createExp +=emitSurfPtcsShape+'.scalePP = rand('+str(scaleMin)+','+str(scaleMax)
        createExp +=');\n'+emitSurfPtcsShape+'.aimRotOffPP = <<rand(-1.0,1.0),0.0,rand(-1.0,1.0)>>;\n'
        createExp +=emitSurfPtcsShape+'.surfRotOffPP = <<0.0,sin(id*rand(50)),cos(id * rand(5))>>;\n'
        
        print createExp
        #build the strings that set the run on dynamics expression
        rbdExp = emitSurfPtcsShape+'.surfRotPP = '+emitSurfPtcsShape+'.surfRotOffPP;\n'
        rbdExp +=emitSurfPtcsShape+'.aimRotPP = '+emitSurfPtcsShape+'.aimRotOffPP;\n'
        print rbdExp
        #update the per particle expressions
        cmds.dynExpression(emitSurfPtcsShape, s = str(createExp), c = 1)
        cmds.dynExpression(emitSurfPtcsShape, s = str(rbdExp), rbd = 1)
        return
    
    def makeDyanmic(self,emitter,emitSurfPtcs):
        '''hook up the particles to the emitters'''
        cmds.connectDynamic(emitSurfPtcs,em=emitter)
        return
        
    def createInstancer(self,insterName,emitSurfPtcsShape):
        '''create the instancer node based on the dress type'''
        print "creating the instancer"
        cmds.particleInstancer(emitSurfPtcsShape, name=insterName, cycle = 'None', cycleStep= 1, cycleStepUnits ='Frames',levelOfDetail='Geometry', rotationUnits ='Radians', rotationOrder= 'XYZ',
                               position= 'worldPosition',age='age')
        cmds.particleInstancer(emitSurfPtcsShape,name=insterName, edit = True,objectIndex = 'indexPP')
        cmds.particleInstancer(emitSurfPtcsShape,name=insterName, edit = True,scale = 'scalePP')
        cmds.particleInstancer(emitSurfPtcsShape,name=insterName, edit = True,aimDirection = 'goalWorldNormal0PP',aimUpAxis = 'surfRotPP')
        dressType = cmds.getAttr(emitSurfPtcsShape+'.dressType')
        if dressType == 'all':
            for geo in cmds.listRelatives('dressExampleGrp', c = True, f = True):
                cmds.particleInstancer(emitSurfPtcsShape,name=insterName, edit = True,addObject=True, object=geo)

        return
        
    def getPtcSetting(self,*args):
        '''query the selected particle systens values, and update the UI'''
        if cmds.ls(sl=True,dag = True, et='particle'):
            selPtc = cmds.ls(sl=True,dag = True, et='particle')
            print "querying particle shape: \"", selPtc[-1],"\""
            ptcCount = cmds.getAttr(selPtc[-1]+".maxCount")
            scaleMin = cmds.getAttr(selPtc[-1]+".scaleMin")
            scaleMax = cmds.getAttr(selPtc[-1]+".scaleMax")
            randSeed = cmds.getAttr(selPtc[-1]+".randSeed")
            #update the gui
            cmds.floatFieldGrp(self.ptcScaleGrp, edit = True, v1 = scaleMin,v2 = scaleMax)
            cmds.intSliderGrp(self.ptcSlider,edit = True, value = ptcCount)
            cmds.textFieldButtonGrp(self.ptcRandGrp, edit = True, text = str(randSeed))
        else:
            print "Select a particle system"
        
        return
    
    def updatePtcSetting(self,*args):
        '''update the selected particle system based on the UI'''
        if cmds.ls(sl=True,dag = True, et='particle'):
            selPtc = cmds.ls(sl=True,dag = True, et='particle')
            ptcCount = cmds.intSliderGrp(self.ptcSlider, query = True, value = True)
            values= cmds.floatFieldGrp(self.ptcScaleGrp, query =True, value = True)
            randSeed = cmds.textFieldButtonGrp(self.ptcRandGrp, query = True, text = True)
            cmds.setAttr(selPtc[-1]+".maxCount",int(ptcCount))
            cmds.setAttr(selPtc[-1]+".scaleMin",float(values[0]))
            cmds.setAttr(selPtc[-1]+".scaleMax",float(values[1]))
            cmds.setAttr(selPtc[-1]+".randSeed",float(float(randSeed)))
            cmds.setAttr(selPtc[-1]+".seed[0]",int(int(randSeed)))
            self.updateParticleBucket(selPtc[-1])
            cmds.currentTime(cmds.playbackOptions( query = True, minTime = True ))
            if not cmds.play( q=True, state=True ):cmds.play( forward=True )
        else:
            print "Select a particle system"
        return
        
    def bakeParticleBucket(self,insterName):
        '''convert the instanced particles to geometry in scene'''
        cmds.select(insterName)
        #call to the outside plug-in nsUninstancer
        mel.eval('nsUninstancer -bakeType "geometry" -frameStep 1 -copyAsInstance 0 '+insterName+';')
        return
        
    def bakeAllBuckets(self,*args):
        #load nsUnInstancer if not already loaded
        #if nothing is selected select all ptcs
        #else iterate on the selected buckets
        #call bakeParticleBucket
        if not cmds.pluginInfo('NimbleTools.py', query=True, loaded=True):
            cmds.loadPlugin( 'NimbleTools.py' )
        lastFrame = cmds.playbackOptions( query = True, maxTime = True )
        cmds.currentTime(lastFrame,edit = True)
        if cmds.ls(sl=True,dag = True, et='instancer'):
            allInst = cmds.ls(sl=True,dag = True, et='instancer')
        else:
            allInst = cmds.ls(et ='instancer')
        for inst in allInst:
            self.bakeParticleBucket(inst)
        
        return
    '''common init for ui'''
    def __init__(self, Title):
        self.title = Title
        self.uiName = Title.strip('')
        self.bttnHght = 40
        self.bttnWdth = 400
        self.numBttns = 10
        self.bttnSpace = self.numBttns * self.bttnHght
        self.wndwHght = self.bttnSpace
        if self.wndwHght > 1000:
            self.wndwHght = 1000
    #global variables for the UI
    defaultPtcCount = 50
    defaultMin = 0.8
    defaultMax = 3.0
    defaultRnd = 1234
    ptcCount = defaultPtcCount
    ptcMin = defaultMin
    ptcMax = defaultMax
    ptcSlider = ''
    ptcScaleGrp = ''
    ptcRandGrp = ''
    def makeNewSeed(self,*args):
        newSeed = random.randrange(100, 360,1)
        cmds.textFieldButtonGrp(self.ptcRandGrp, edit = True, text = str(newSeed))
        
        return 
        
    def create(self):
        '''creates the initial UI'''
        if cmds.window(self.uiName, exists=True):
            cmds.deleteUI(self.uiName)
        cmds.window(self.uiName, title=self.title)
        self.mainScroll = cmds.scrollLayout(vst = 0, hst = 0) 
        self.mainCol = cmds.columnLayout(adjustableColumn=True)
        cmds.button(l = 'import dress kit', h = self.bttnHght, w = self.bttnWdth,
                    c= self.importDressRigFile , ann = 'import dress kit', p=self.mainCol)
        cmds.button(l = 'add dress to selected', h = self.bttnHght, w = self.bttnWdth,
                    c= self.addDressToSelected , ann = 'add dress to selected', p=self.mainCol)
        self.ptcSlider = cmds.intSliderGrp( field=True, label='particleCount', 
                                       w = self.bttnWdth, 
                                       minValue=0, maxValue=500, fieldMinValue=0, 
                                       fieldMaxValue=100, value= self.defaultPtcCount)
        self.ptcScaleGrp = cmds.floatFieldGrp( nf=2, label='Scale Min / Max ',
                                               value1=self.defaultMin, value2=self.defaultMax)
        self.ptcRandGrp = cmds.textFieldButtonGrp( label='RandomSeed', 
                                                   text=str(self.defaultRnd), buttonLabel='New Seed',
                                                   bc = self.makeNewSeed)
        cmds.button(l = 'get ptc settings', h = self.bttnHght, w = self.bttnWdth,
                    c= self.getPtcSetting , ann = 'query the specific ptc\'s settings ', p=self.mainCol)                                      
        cmds.button(l = 'update ptc system', h = self.bttnHght, w = self.bttnWdth,
                    c= self.updatePtcSetting , ann = 'update the settings of the ptc', p=self.mainCol)
        cmds.button(l = 'add 3d paint texture to surface', h = self.bttnHght, w = self.bttnWdth,
                c= self.addShaderToSelected , ann = 'add a new shading network to paint interactively with', p=self.mainCol)           
        cmds.button(l = 'connect texture to emitter', h = self.bttnHght, w = self.bttnWdth,
                c= self.connectTextureToEmitter , ann = 'use the white of the texture for emmission', p=self.mainCol)           
        cmds.button(l = 'disconnect texture to emitter', h = self.bttnHght, w = self.bttnWdth,
                c= self.disconnectTextureFromEmitter , ann = 'disable using the texture map', p=self.mainCol)           
        cmds.button(l = 'bake Instaces to geo', h = self.bttnHght, w = self.bttnWdth,
                    c= self.bakeAllBuckets , ann = 'add dress to selected', p=self.mainCol)
        
        cmds.showWindow(self.uiName)
        cmds.window(self.uiName, edit=True, width=self.bttnWdth+50, height=self.wndwHght)
        


def run():
    '''create the dress UI'''
    newWin = dressUi('shotDressExample')
    newWin.create()

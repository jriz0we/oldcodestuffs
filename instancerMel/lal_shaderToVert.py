#Copyright (c) 2004-2010 Lucasfilm Ltd. All rights reserved. Used under
#authorization. This material contains the confidential and proprietary
#nformation of Lucasfilm Ltd. and may not be copied in whole or in part
#without the express written permission of Lucasfilm Ltd. This copyright
#notice does not imply publication.
#
# created by Josh Rowe
# October 2009
#
# LAL created script for asset production.
# the lambert shaders are converted to vertex colors
# this can be used for model assets and rigged geo as well
# required for Season 3 best practices

import maya.cmds as mc
def run():
    try:
        selection = mc.ls(selection =True) #list of selected
        for surface in selection:
            print 'working on surface:',surface
            mc.select(surface)
            mc.hyperShade(smn = True) #find shaders attached to surface
            shaders = mc.ls(selection =True) #list from selected
            print 'there are ',len (shaders), 'shaders:', shaders
            cmdList =[]
            for singleSh in shaders: #for each shader attach to the surface
                diffClr = singleSh + '.color'
                incClr = singleSh + '.incandescence'
                transClr =singleSh + '.transparency'
                shDiff = mc.getAttr(diffClr)
                shInc = mc.getAttr(incClr)
                shTrans= mc.getAttr(transClr)
                incGain = 1.8 #increased this till the resulting vertex color looked close to the shader
                trans= 0.0 #opaque
                modInc=[]
        
                for foo in range(3): #goofy tuple data "adjustment"
                    modInc.append((shInc[0][foo]*incGain))
                    if (shTrans[0][foo] > 0.0) or (shTrans[0][foo] > trans): #if there is any transparency set to the largest value
                        trans = shTrans[0][foo]
        
                trans = 1.0 - trans #flip value for shaders -> vertex alpha
                shColor = ((shDiff[0][0] + modInc[0]),(shDiff[0][1] + modInc[1]),(shDiff[0][2] + modInc[2]))
                print 'working on shader:',singleSh, ' with a final color of :', shColor, " alpha:",trans
                mc.select(singleSh)
                mc.hyperShade(objects = singleSh) #returns a selection of surfaces, can include more than selected surface
                comps = mc.ls(selection =True) #list of components with singleSh
                print comps
                mc.select(cl=True)#clear selection
                surfaceOnly=[] #new var of components on the selected surface ONLY
                for foo in comps:
                    if foo == mc.listRelatives(surface)[0]:#if the entire surface has this shader, the surface"Shape" is returned from mc.hyperShade
                        surfaceOnly.append(surface) #add to list
                    elif foo.startswith(surface): #if part of parent surface, add to list
                        surfaceOnly.append(foo)
                cmdTuple=(shColor,trans,surfaceOnly) #combo of color, transparency, and componets to apply current shader to
                cmdList.append(cmdTuple)
            mc.select(surface)
            mc.hyperShade(assign='initialShadingGroup')#reset surface to lambert1
            for cmd in cmdList:#apply data to geo
                print 'color to be applied:',cmd[0]
                print 'surfaces and components to be vertpainted',cmd[2]
                mc.select(cmd[2])
                mc.polyColorPerVertex( rgb=cmd[0],a=cmd[1], cdo=True )
    except:
       print 'Error'
    finally:
       print "shader to vertex coloring complete" 

#!/usr/bin/env python2

# Copyright (c) 2012 Lucasfilm Ltd. All rights reserved. Used under
# authorization. This material contains the confidential and proprietary
# information of Lucasfilm Ltd. and may not be copied in whole or in part
# without the express written permission of Lucasfilm Ltd. This copyright
# notice does not imply publication.

import hashlib
import maya.cmds as cmds

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
    return  '|'.join(dagParts)

def nodeIsVisible(nodeToCheck):
    """docstring for nodeIsVisible"""
    #node exists
    if nodeToCheck in cmds.ls(v = True, l = True, ni = True):
        return  True

def addHashIDandShaderInfo(nodeToUpdate, stripNamespaces):
    """docsting for addHashIDandShaderInfo"""
    #add hash id
    if not cmds.attributeQuery( 'ABC_hash', node= nodeToUpdate, ex=True ):
        cmds.addAttr(nodeToUpdate, shortName='ABC_hash', dataType='string')
    tHash = hashlib.md5()
    hashName = _remove_namespace_from_dag_path(nodeToUpdate)
    tHash.update(str(hashName))
    cmds.setAttr(nodeToUpdate+'.ABC_hash', tHash.hexdigest(), type = 'string')
    #get the shaders assigned to the node, purely for debug or manual assignment
    renderSetList = cmds.listSets(object = nodeToUpdate, type = 1, extendToShape = True)
    renderSetList = [_remove_namespace_from_dag_path(sg) for sg in renderSetList]
    #if for some reason a mesh doesnt have a shader just skip it
    if renderSetList == None: return
    if not cmds.attributeQuery('ABC_sglist', node= nodeToUpdate, ex=True ):
        cmds.addAttr(nodeToUpdate, shortName = 'ABC_sglist', dataType = 'string')
    sgList = ';'.join(renderSetList)
    cmds.setAttr(nodeToUpdate+'.ABC_sglist', sgList, type = 'string')
    #starting to get clever with functions in list comprehensions
    return tHash.hexdigest()
    
def determineExportGeomFromTopNode(cacheJob):
    """docstring for determineExportGeomFromTopNode"""
    geomObjectList = []
    #find all render geom from under topNode
    tpKids = cmds.listRelatives(cacheJob.topNode, ad = True, f = True, type = ['mesh','nurbsSurface'])
    #filer list to visible only
    geomList = [kid for kid in tpKids if nodeIsVisible(kid)]
    geomNameList = [_remove_namespace_from_dag_path(node) for node in geomList]
    #add abc_hash and abc_sglist attributes to each node and get a list of those values
    hashList = [addHashIDandShaderInfo(node,cacheJob.jobOptions['stripNamespaces']) for node in geomList]
    for i in range(len(geomList)):
        geomObj = {}
        geomObj['dagpath'] = geomList[i]
        geomObj['name'] = geomNameList[i]
        geomObj['hash'] = hashList[i]
        geomObj['index'] = i
        geomObjectList.append(geomObj)
    #return geomObjectList, geomNameList, hashList
    return geomObjectList

def importedGeoList(importJob):
    """docstring for importedGeoList"""
    geomList = cmds.listRelatives(importJob.jobNode, ad = True, f = True, type = ['mesh','nurbsSurface'])
    return geomList

    


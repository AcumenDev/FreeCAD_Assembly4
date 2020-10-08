#!/usr/bin/env python3
# coding: utf-8
#
# LGPL
# Copyright HUBERT Zoltán
#
# newDatumCmd.py 



import os

from PySide import QtGui, QtCore
import FreeCADGui as Gui
import FreeCAD as App
import Part

import libAsm4 as Asm4



"""
    +-----------------------------------------------+
    |      a class to create all Datum objects      |
    +-----------------------------------------------+
"""
class newDatum:
    "My tool object"
    def __init__(self, datumName):
        self.datumName = datumName
        # recognised types
        self.datumTypes = ['PartDesign::Point','PartDesign::Line','PartDesign::Plane','PartDesign::CoordinateSystem']
        self.containers = [ 'App::Part', 'PartDesign::Body', 'App::DocumentObjectGroup']
        if self.datumName   == 'Point':
            self.datumType   = 'PartDesign::Point'
            self.menutext    = "New Point"
            self.tooltip     = "Create a new Datum Point in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Point.svg')
            self.datumColor  = (0.00,0.00,0.00)
            self.datumAlpha  = []
        elif self.datumName == 'Axis':
            self.datumType   = 'PartDesign::Line'
            self.menutext    = "New Axis"
            self.tooltip     = "Create a new Datum Axis in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Axis.svg')
            self.datumColor  = (0.00,0.00,0.50)
            self.datumAlpha  = []
        elif self.datumName == 'Plane':
            self.datumType   = 'PartDesign::Plane'
            self.menutext    = "New Plane"
            self.tooltip     = "Create a new Datum Plane in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Plane.svg')
            self.datumColor  = (0.50,0.50,0.50)
            self.datumAlpha  = 80
        elif self.datumName == 'LCS':
            self.datumType   = 'PartDesign::CoordinateSystem'
            self.menutext    = "New Coordinate System"
            self.tooltip     = "Create a new Coordinate System in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_CoordinateSystem.svg')
            self.datumColor  = []
            self.datumAlpha  = []
        elif self.datumName == 'Sketch':
            self.datumType   = 'Sketcher::SketchObject'
            self.menutext    = "New Sketch"
            self.tooltip     = "Create a new Sketch in a Part"
            self.icon        = os.path.join( Asm4.iconPath , 'Asm4_Sketch.svg')
            self.datumColor  = []
            self.datumAlpha  = []


    def GetResources(self):
        return {"MenuText": self.menutext,
                "ToolTip": self.tooltip,
                "Pixmap" : self.icon }


    def IsActive(self):
        if App.ActiveDocument:
            # is something correct selected ?
            if self.checkSelection():
                return(True)
        return(False)


    def checkSelection(self):
        # if something is selected ...
        if Gui.Selection.getSelection():
            selectedObj = Gui.Selection.getSelection()[0]
            # ... and it's an App::Part or an datum object
            if selectedObj.TypeId in self.containers or selectedObj.TypeId in self.datumTypes:
                return(selectedObj)
        return None



    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        # check that we have somewhere to put our stuff
        selectedObj = self.checkSelection()
        
        # check whether we have selected a container
        if selectedObj.TypeId in self.containers:
            parentContainer = selectedObj
        # if a datum object is selected we try to find the parent container
        elif selectedObj.TypeId in self.datumTypes:
            parent = selectedObj.getParentGeoFeatureGroup()
            if parent.TypeId in self.containers:
                parentContainer = parent
        # something went wrong
        else:
            Asm4.warningBox("I can't create a "+self.datumType+" with the current selections")
            
        # check whether there is already a similar datum, and increment the instance number 
        # instanceNum = 1
        #while App.ActiveDocument.getObject( self.datumName+'_'+str(instanceNum) ):
        #    instanceNum += 1
        #datumName = self.datumName+'_'+str(instanceNum)
        if parentContainer:
            # input dialog to ask the user the name of the Sketch:
            proposedName = Asm4.nextInstance( self.datumName, startAtOne=True )
            text,ok = QtGui.QInputDialog.getText(None,'Create new '+self.datumName,
                    'Enter '+self.datumName+' name :'+' '*40, text = proposedName)
            if ok and text:
                # App.activeDocument().getObject('Model').newObject( 'Sketcher::SketchObject', text )
                createdDatum = parentContainer.newObject( self.datumType, text )
                # automatic resizing of datum Plane sucks, so we set it to manual
                if self.datumType=='PartDesign::Plane':
                    createdDatum.ResizeMode = 'Manual'
                    createdDatum.Length = 100
                    createdDatum.Width = 100
                # if color or transparency is specified for this datum type
                if self.datumColor:
                    Gui.ActiveDocument.getObject(createdDatum.Name).ShapeColor = self.datumColor
                if self.datumAlpha:
                    Gui.ActiveDocument.getObject(createdDatum.Name).Transparency = self.datumAlpha
                # highlight the created datum object
                Gui.Selection.clearSelection()
                Gui.Selection.addSelection( App.ActiveDocument.Name, parentContainer.Name, createdDatum.Name+'.' )
                Gui.runCommand('Part_EditAttachment')



"""
    +-----------------------------------------------+
    |      a class to create an LCS on a hole       |
    +-----------------------------------------------+
"""
class newHole:
    def GetResources(self):
        return {"MenuText": "New Hole Axis",
                "ToolTip": "Create a Datum Axis attached to a hole",
                "Pixmap" : os.path.join( Asm4.iconPath , 'Asm4_Hole.svg')
                }

    def IsActive(self):
        selection = self.getSelection()
        if selection == None:
            return False
        else:
            return True

    def getSelection(self):
        # check that we have selected a circular edge
        selection = None
        if App.ActiveDocument:
            # 1 thing is selected:
            if len(Gui.Selection.getSelection()) == 1: 
                # check whether it's a circular edge:
                edge = Gui.Selection.getSelectionEx()[0]
                if len(edge.SubObjects) == 1:
                    # if the edge is circular
                    if Asm4.isCircle(edge.SubObjects[0]):
                        # find the feature on which the edge is located
                        parentObj = Gui.Selection.getSelection()[0]
                        edgeName = edge.SubElementNames[0]
                        # selection = ( parentObj, edgeName )
                        selection = ( parentObj, edge )
        return selection

    """
    +-----------------------------------------------+
    |                 the real stuff                |
    +-----------------------------------------------+
    """
    def Activated(self):
        ( selectedObj, edge ) = self.getSelection()
        edgeName = edge.SubElementNames[0]
        parentPart = selectedObj.getParentGeoFeatureGroup()
        # if the solid having the edge is indeed in an App::Part
        if parentPart and (parentPart.TypeId=='App::Part' or parentPart.TypeId=='PartDesign::Body'):
            # check whether there is already a similar datum, and increment the instance number 
            instanceNum = 1
            while App.ActiveDocument.getObject( 'HoleAxis_'+str(instanceNum) ):
                instanceNum += 1
            axis = parentPart.newObject('PartDesign::Line','HoleAxis_'+str(instanceNum))
            axis.Support = [( selectedObj, (edgeName,) )]
            axis.MapMode = 'AxisOfCurvature'
            axis.MapReversed = False
            axis.ResizeMode = 'Manual'
            axis.Length = edge.SubObjects[0].BoundBox.DiagonalLength
            axis.ViewObject.ShapeColor = (0.0,0.0,1.0)
            axis.ViewObject.Transparency = 50
            '''
            pt1    = App.Vector(0,0,diam/2.)
            pt2    = App.Vector(0,0,-diam/2.)
            axis   = parentPart.newObject('Part::FeaturePython', 'HoleAxis_'+str(instanceNum))
            axis.ViewObject.Proxy = Asm4.setCustomIcon(axis,'Asm4_Hole.svg')
            axis.Shape = Part.Wire(Part.makeLine(pt1,pt2))
            axis.Placement = circle.Placement
            axis.ViewObject.DrawStyle = 'Dashdot'
            axis.ViewObject.LineColor = (0.0,0.0,1.0)
            '''
            axis.recompute()
            parentPart.recompute()



"""
    +-----------------------------------------------+
    |       add the commands to the workbench       |
    +-----------------------------------------------+
"""
Gui.addCommand( 'Asm4_newPoint', newDatum('Point') )
Gui.addCommand( 'Asm4_newAxis',  newDatum('Axis')  )
Gui.addCommand( 'Asm4_newPlane', newDatum('Plane') )
Gui.addCommand( 'Asm4_newLCS',   newDatum('LCS')   )
Gui.addCommand( 'Asm4_newSketch',newDatum('Sketch'))
Gui.addCommand( 'Asm4_newHole',  newHole()         )


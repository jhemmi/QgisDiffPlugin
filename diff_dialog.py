# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DiffDialog
                                 A QGIS plugin
 Diff between a vector and a text file
                             -------------------
        begin                : 2015-06-24
        git sha              : $Format:%H$
        copyright            : (C) 2015 by jhemmi.eu
        email                : jean@jhemmi.eu
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4 import QtGui, uic  # for Form_class
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Import system & os
import os.path
import sys, string
import platform

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'diff_dialog_base.ui'))

DIFF_TRACE = "Yes" # "Yes" pour tracer
SEPARATORS = [ ";", "\t", "|", ","]
SEPARATORS_PRINT = [ ";", "TAB", "|", ","]
 
class DiffDialog(QtGui.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(DiffDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        # Slot for boutons 
        self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        
        # Slot for fields & text file
        self.inputLayerComboONE.currentIndexChanged[int].connect( self.update_field_list )
        self.toolFileButtonOTHER.pressed.connect( self.input_textfile )  

        self.diff_log( "Your machin runs a " + platform.system() + " operating system")
        # Creating vector list in combo
        self.create_vector_list()
        
    # MESSAGES & LOG
    def diff_message_box( self, text, level ="warning", title="DIFF plugin",):
        """Send a message box by default Warning"""
        if level == "about":
            QMessageBox.about( self, title, text)
        elif level == "information":
            QMessageBox.information( self, title, text)
        else:
            QMessageBox.warning( self, title, text)

##    def showHelp(self):
##""" TODO Help html""" 
## TODO à creer
##        file = inspect.getsourcefile(ContourDialog)
##        file = 'file://' + os.path.join(os.path.dirname(__file__),'html/index.html')
##        file = file.replace("\\","/")
##        self._iface.openURL(file,False)

    def diff_log( self, aText, level ="WARNING"):
        """Send a text to the Diff log"""
        if DIFF_TRACE == "Yes":
            QgsMessageLog.logMessage( aText, "Diff log", QgsMessageLog.WARNING)      

    def diff_write_in_list( self, aText):
        """Write a text in the results list"""
        if platform.system() == "Windows":
            info = aText.split( "\r\n" )        
        else:
             info = aText.split( "\n" )        
        self.listWidget.addItems( info )
                
    # VECTORS
    def create_vector_list( self ):
        """Create a list of vector and initialize the comboONE"""
        layers = self.get_vector_layers()
        if len( layers) == 0:
            self.diff_log( "DIFF create_vector_list> No layer")
            # TODO throw a box and remove dialog
        self.inputLayerComboONE.addItems( layers )
        self.inputLayerComboONE.setCurrentIndex( 0)

    def get_vector_layers( self ):
        """Create a list of vector """
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        layerList = []
        for name, layer in layerMap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer:
                layerList.append( layer.name() )
        return layerList
                
    # FIELDS
    def update_field_list( self ):
        """ Create a list of fields for the current vectorin fieldCombo Box"""
        inputLayer = str(self.inputLayerComboONE.itemText(self.inputLayerComboONE.currentIndex()))
        self.fieldComboONE.clear()
        layer = self.get_layer_by_name( inputLayer )
        if layer is not None:
            self.diff_log( "Look for fields of layer >" + layer.name())
            for index, field in enumerate(layer.dataProvider().fields()):
                self.fieldComboONE.addItem( str( field.name()) )
        else:
            self.fieldComboONE.addItem( "No field found")
            
    def get_layer_by_name( self, layerName ):
        layerMap = QgsMapLayerRegistry.instance().mapLayers()
        for name, layer in layerMap.iteritems():
            if layer.type() == QgsMapLayer.VectorLayer and layer.name() == layerName:
                # The layer is found
                break
        if layer.isValid():
            return layer
        else:
            return none
        
        
    # TEXT FILE
    def input_textfile( self ):
        """ Catch name of text file """
        fileName = QFileDialog.getOpenFileName(None, "Select your Text File:", "", "*.csv *.txt")
        if len( fileName) == 0:
          return
        self.editOTHERfile.setText( fileName )
        #  open other file and find the best separator in the first line
        fields = []
        bestSeparator, fields = self.get_file_fields ( fileName)

        # Proposing the best separator in dialog
        self.editSeparateur.setText( bestSeparator )
        # and fields names
        self.fieldComboOTHER.clear()
        for i in range( len(fields)):
            self.fieldComboOTHER.addItem( fields[i] )

    def get_file_fields( self, afile ):
        """ Create list of fields in first line of Text File"""
        # Look for fields in a text file
        self.diff_log( "ENCODE " + str( sys.getdefaultencoding()))
        a_list = []

        # Open
        a_file = open( afile, 'r')
        a_list = a_file.readlines()
        first_line = a_list[ 0][:-1]   # Avoid last car
        another_line = a_list[ int( len( a_list) / 2)][:-1]
        a_file.close()    
        self.diff_log( "Premiere ligne fichier >" + first_line)

        # Look for separator
        the_separator, the_separator_print = self.get_separator ( first_line)
        if the_separator == "NO SEP FOUND":
            return "NO SEP FOUND", []

        # Verify separator in another line
        another_separator, another_separator_print = self.get_separator ( another_line, 1)
        if the_separator == another_separator:
            self.diff_log( "Separators look good")
        else:
            self.diff_log( "Separators seem to be inconsistant>" + the_separator +
                                    "< >" + another_separator)        
            self.diff_message_box( "Mind yourself separators in text file seem inconsistant",
                               "information" )

        # Look for fields
        fields_name = string.split( first_line, the_separator)    
        self.diff_log( "Fields >" + str( fields_name))
        return the_separator_print, fields_name

    def get_separator( self, aline, recall = 0 ):
        """ Look for a separator in text file"""
        # Look for separator in a text file
        num_tok = []
        for i in range( len( SEPARATORS)):
            num_token = string.count( aline , SEPARATORS[ i])
            num_tok.append( num_token)
 
        # Best separator
        if max( num_tok) == 0:
            return "NO SEP FOUND", "NO SEP FOUND"
        the_separator = SEPARATORS[ num_tok.index( max( num_tok))]
        the_separator_print = SEPARATORS_PRINT[ num_tok.index( max( num_tok))]
        if recall == 0:
            self.diff_log( "Best separator >" + the_separator_print)
        return the_separator, the_separator_print

    def get_file_field_values( self, afile, field, separator):
        """Look for a field's values in a text file"""
        a_list = []

        # Open
        a_file = open( afile, 'r')
        a_list = a_file.readlines()

        fields_name = string.split( a_list[ 0][:-1], separator)
        #self.diff_log( " fields " + str( fields_name))

        for i in range( 0, len ( fields_name)):
            if fields_name[ i] == field:
                pos = i
                break

        self.diff_log( "Field is " + field + " in position " + str( pos))

        found = []
        for a_line in a_list[ 1:]:
            # Look for fields using separator
            fields_val = string.split( a_line[:-1], separator)
            found.append( fields_val[ pos])
                    
        # Close
        a_file.close()

        return found

    def reject( self ):
        """Close when bouton is Cancel"""
        QDialog.reject( self )

    def accept( self ):
        """Verify when bouton is OK"""
        pass
        if self.inputLayerComboONE.currentText() == "":
            return QMessageBox.information( self, self.tr( "Diff vector/txt" ),
                                   self.tr( "No input layer specified" ) )
        elif self.editOTHERfile.text() == "":
            QMessageBox.information( self, self.tr( "Diff vector/txt" ),
                                   self.tr( "Please specify other file" ) )
        else:
          
            self.listWidget.clear()
            oneField = self.fieldComboONE.currentText()
            oneLayer = self.get_layer_by_name( self.inputLayerComboONE.currentText())
            otherFile = self.editOTHERfile.text()
            otherField = self.fieldComboOTHER.currentText()
            separator_print = self.editSeparateur.text()
            # Find separator position
            position = SEPARATORS_PRINT.index( separator_print) 
            #self.diff_log( "Position in SEPARATORS_PRINT " + str( position))
            separator = SEPARATORS[ position]
            self.diff_log( "Position in SEPARATORS is " + str( separator))
            QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
            # TODO self.btnOk.setEnabled( False )
            self.jhemmi_DIFF( oneLayer, oneField, otherFile, otherField, separator)
            
##            self.iface.messageBar().pushMessage(
##                "DIFF plugin",
##                "End of diff, see you later",
##                level=QgsMessageBar.INFO)          
            self.diff_message_box( self.tr( "End of DIFF, see you later"), "information" )
            # TODO 
            self.restoreGui()
          

    def restoreGui( self ):
        QApplication.restoreOverrideCursor()
        self.btnOk.setEnabled( True )
        return
        
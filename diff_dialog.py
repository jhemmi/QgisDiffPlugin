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
from PyQt4.QtCore import QSettings
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *

# Import system & os
import os.path
import sys, string
import platform
if platform.system() == 'Windows':
    import win32api
    
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'diff_dialog_base.ui'))
    
# TODO: pour V1 Deux fenetres opur les 2 comparaisons ?
# TODO: pour V1 Ajouter autres attributs dans la fenetre résultats.

DIFF_TRACE = "Yes" # "Yes" for tracking
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
        self.plugin_dir = os.path.dirname(__file__)  

              
        # Slot for boutons 
        self.refreshButton.pressed.connect(self.create_vector_list )
        self.buttonBox.button( QDialogButtonBox.Ok ).pressed.connect(self.accept)
        self.buttonBox.button( QDialogButtonBox.Cancel ).pressed.connect(self.reject)
        self.buttonBox.button( QDialogButtonBox.Help ).pressed.connect(self.helpRequested)
            
        # Slot for fields & text file
        self.inputLayerComboONE.currentIndexChanged[int].connect( self.update_field_list_ONE )
        self.inputLayerComboONE.currentIndexChanged[int].connect( self.update_field_list_TWO )
        self.toolFileButtonOTHER.pressed.connect( self.input_textfile )  
        self.diff_log( "Your machin runs a " + platform.system() + " operating system")

##        # Memorising the project
##        titleProject = QgsProject.instance().title()
##        filenameProject = QFileInfo( QgsProject.instance().fileName())
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
        for aInfo in info:
            self.textEdit.insertPlainText( aInfo + "\n")   
                                        
    # VECTORS
    def create_vector_list( self ):
        """Create a list of vector and initialize the comboONE"""
        layers = self.get_vector_layers()
        if len( layers) == 0:
            self.inputLayerComboONE.setCurrentIndex( 0)
            self.diff_log( "DIFF create_vector_list> No layer")
        self.inputLayerComboONE.clear( )
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
    def update_field_list_ONE( self ):
        """ Create a list of fields having unique values for the current vector in fieldCombo Box"""
        inputLayer = str(self.inputLayerComboONE.itemText(self.inputLayerComboONE.currentIndex()))
        self.fieldComboONE.clear()
        layer = self.get_layer_by_name( inputLayer )
        if layer is not None:
            self.diff_log( "Look for fields of layer >" + layer.name())
            for index, field in enumerate(layer.dataProvider().fields()):
                # Vérifier si les valeurs du field name sont unique
                valeur_unique = "YES"
                valeur_dic = {}
                mon_nom = field.name()
                #idx = layer.fieldNameIndex(mon_nom)
                k = 0
                iter = layer.getFeatures()
                for feature in iter:
                    try:
                        if feature.attributes()[index] == None:
                            valeur_unique = "NO"
                        elif valeur_dic.has_key( feature.attributes()[index]) ==1:
                            valeur_unique = "NO"
                        else:
                            valeur_dic[ feature.attributes()[index]] = k
                    except:
                        valeur_unique = "NO"
                    if valeur_unique == "NO":
                        break
                    k = k+1
                    
                if valeur_unique == "YES":
                    self.fieldComboONE.addItem( str( field.name()) )
        else:
            self.fieldComboONE.addItem( "No field found")

        
    def update_field_list_TWO( self ):
        """ Create a list of fields for the current vector in fieldCombo_TWO Box"""
        inputLayer = str(self.inputLayerComboONE.itemText(self.inputLayerComboONE.currentIndex()))
        # Eviter le champ de field ONE
        aFieldONE = str(self.fieldComboONE.itemText(self.fieldComboONE.currentIndex()))
        self.fieldComboTWO.clear()
        layer = self.get_layer_by_name( inputLayer )
        if layer is not None:
            self.diff_log( "Look for fields of layer >" + layer.name())
            for index, field in enumerate(layer.dataProvider().fields()):
                if ( str( field.name()) != aFieldONE):
                    self.fieldComboTWO.addItem( str( field.name()) )
        else:
            self.fieldComboTWO.addItem( "No field found")
        
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
        fileName = QFileDialog.getOpenFileName(None, 
            "Select your Text File:",
            "", "*.csv *.txt")
        if len( fileName) == 0:
          return
        self.editOTHERfile.setText( fileName )
        #  open other file and find the best separator in the first line
        fields = []
        bestSeparator, fields = self.get_file_fields ( fileName)

        # Proposing the best separator in dialog
        self.editSeparateur.setText( bestSeparator )
        # and fields names
        self.fieldComboTEXT.clear()
        self.fieldComboOTHER.clear()
        for i in range( len(fields)):
            self.fieldComboTEXT.addItem( fields[i] )
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
        self.diff_log( "Fields >" + str( fields_name) + "<")
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

    def get_file_field_values( self, afile, field, secondField, separator):
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
        for j in range( 0, len ( fields_name)):
            if fields_name[ j] == secondField:
                posSecond = j
                break

        #self.diff_log( "Field " + field + " is in position " + str( pos))

        found = []
        foundSecond = []
        for a_line in a_list[ 1:]:
            # Look for fields using separator
            fields_val = string.split( a_line[:-1], separator)
            found.append( fields_val[ pos])
            foundSecond.append( fields_val[ posSecond])
                    
        # Close
        a_file.close()

        return found, foundSecond

    # Slots
    def helpRequested(self):
        """ Help html""" 
        # file = inspect.getsourcefile( Diff)
        help_url = QUrl("file:///%s/help/index.html" % self.plugin_dir)
        QDesktopServices.openUrl(help_url)

    def reject( self ):
        """Close when bouton is Cancel"""
        self.textEdit.clear()
        QDialog.reject( self)
                
    def accept( self ):
        """Verify when bouton is OK"""
        if self.inputLayerComboONE.currentText() == "":
            return QMessageBox.information( self, self.tr( "Diff vector/txt" ),
                                   self.tr( "No input layer specified" ) )
        elif self.editOTHERfile.text() == "":
            QMessageBox.information( self, self.tr( "Diff vector/txt" ),
                                   self.tr( "Please specify other file" ) )
        else:
          
            self.textEdit.clear()
            oneField = self.fieldComboONE.currentText()
            secondOneField = self.fieldComboTWO.currentText()
            oneLayer = self.get_layer_by_name( self.inputLayerComboONE.currentText())
            otherFile = self.editOTHERfile.text()
            otherField = self.fieldComboTEXT.currentText()
            secondOtherField = self.fieldComboOTHER.currentText()
            separator_print = self.editSeparateur.text()
            # Find separator position
            position = SEPARATORS_PRINT.index( separator_print) 
            #self.diff_log( "Position in SEPARATORS_PRINT " + str( position))
            separator = SEPARATORS[ position]
            self.diff_log( "Position in SEPARATORS is " + str( separator))
            # QApplication.setOverrideCursor( QCursor( Qt.WaitCursor ) )
            # TODO 
            self.buttonBox.button( QDialogButtonBox.Ok ).setEnabled( False )
            self.jhemmi_DIFF( oneLayer, oneField, secondOneField, 
                otherFile, otherField, secondOtherField, separator)
            
##            self.iface.messageBar().pushMessage(
##                "DIFF plugin",
##                "End of diff, see you later",
##                level=QgsMessageBar.INFO)          
            self.diff_message_box( self.tr( "End of DIFF, see you later"), "information" )
        # In all case Gui is back in the inital state 
        self.restoreGui()
          

    def restoreGui( self ):
        # QApplication.restoreOverrideCursor()
        self.buttonBox.button( QDialogButtonBox.Ok ).setEnabled( True )
        return
    
    def jhemmi_DIFF( self, layer, field, secondField, fileName, fieldInFile, secondInFile, separator):
        """Real diff is here"""

        self.diff_write_in_list( 'Compared fields are "' + field +
                                  '" in vector and "'+ fieldInFile + '" in TextFile')

        ### Find list of values in one Vector File
        # get unique values in field
        uniqueValues = []
        secondValues = []
        for ft in layer.getFeatures():
            if ft[ field ] not in uniqueValues:
                uniqueValues.append( ft[ field])
                secondValues.append( ft[ secondField])
                
        ### Find list of values in other File
        fileValues, fileSecondValues = self.get_file_field_values( fileName, fieldInFile, \
                secondInFile, separator)

        # Which Radio bouton is checked :  
        if self.radioButton_1.isChecked():
            # Compare list ONE not in OTHER
            self.diff_log( " COMPARE>" + "Diff vector not in text file")
            apriori = "OUI"
            erreur = []
            for iv in range( len( uniqueValues )):
                if uniqueValues[ iv] not in fileValues:
                    #self.diff_log( "Line of vector >" + 
                    #    uniqueValues[iv] + "< is not in file")   
                    apriori = "NON"
                    aText = str( uniqueValues[iv]) + " ~ " + str( secondValues[iv])
                    # OLD erreur.append( str( uniqueValues[iv]))
                    erreur.append( aText)
            if apriori == "OUI":
                self.diff_write_in_list( "All in the Vector are in the TextFile") 
            else:
                self.diff_write_in_list( 'Second field in vector is "' + secondField + '"')
                self.diff_write_in_list( "Number of differences ==> " + 
                    str( len(erreur))+ " <== ")
                sortie_trie = sorted( erreur)
                for i in range( len( sortie_trie)):
                    self.diff_write_in_list( str( sortie_trie[ i]))
          
        elif self.radioButton_2.isChecked():
            # Compare list OTHER NOT in ONE
            self.diff_log( " COMPARE>" + "Diff text file not in vector")
            apriori = "OUI"
            erreur = []
            for iv in range( len(fileValues)):
                if fileValues[ iv] not in uniqueValues:
                    #self.diff_log( "Line of file >" + 
                    #    fileValues[iv] + "< is not in vector")   
                    apriori = "NON"
                    aText = str( fileValues[iv]) + " ~ " + str( fileSecondValues[iv])
                    erreur.append( aText)
            if apriori == "OUI":
                self.diff_write_in_list( "All in the TextFile value are in the Vector") 
            else:
                self.diff_write_in_list( 'Second field in textfile is "' + secondInFile + '"')
                self.diff_write_in_list( "Number of differences ==> " + 
                    str( len(erreur))+ " <== ")
                sortie_trie = sorted( erreur)
                for i in range( len( sortie_trie)):
                    self.diff_write_in_list( str( sortie_trie[ i]))
        else:
            self.diff_log( " COMPARE>" + "Diff vector/txt: No other option implemented")
        return

# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GisGrimeFocus
                                 A QGIS plugin
 ass
                              -------------------
        begin                : 2016-10-02
        git sha              : $Format:%H$
        copyright            : (C) 2016 by as
        email                : s
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
import os.path
import sys
import processing
# Initialize Qt resources from file resources.py
import resources
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt4.QtGui import QAction, QIcon,QFileDialog

# Import the code for the dialog
from PyQt4.QtGui import* # para el QMessageBox y el filedialog
from qgis._core import * # para los obejetos de gis como el layer
from qgis.gui import *  # para que funcione QgsMapLayerProxyModel
from GisGrimeFocus_dialog import GisGrimeFocusDialog


class GisGrimeFocus:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """

        """ here the global variables"""
        self.ruta_salida = ""
        self.years = []


        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GisGrimeFocus_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&GisGrimeFocus')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'GisGrimeFocus')
        self.toolbar.setObjectName(u'GisGrimeFocus')


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GisGrimeFocus', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = GisGrimeFocusDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)
        ###########aca las conexiones a los botones############################
        # funcion que guarda la ruta del archivo de salida en el text
        # correspondiente
        self.dlg.pBSearchFile.clicked.connect(self.readInputData)
        self.dlg.pb_calcular_radio.clicked.connect(self.calc_radio)
        self.dlg.pb_calc_kernel.clicked.connect(self.kernel_gausiano)

        #funcionque conecta al boton con la funcion de convertir el scv en shape
        #  y cargarlo
        self.dlg.pBImport.clicked.connect(self.csv_to_shape)
        self.dlg.pb_exportByYear.clicked.connect(self.export_by_date)
        self.dlg.mcb_lista_csv.layerChanged.connect(self.load_fields)


        self.dlg.pushButton.clicked.connect(self.get_years_values)






        return action


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/GisGrimeFocus/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'GisGrimeFocus'),
            callback=self.run,
            parent=self.iface.mainWindow())

        """ se fijan los filtros de los combos """
        # el filtro de NoGeometry
        self.dlg.mcb_lista_csv.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.load_fields()  # set the current layer  and load the fields


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&GisGrimeFocus'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar


    def run(self):
        """Run method that performs all the real work"""
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def readInputData(self):

        #abre el dialog para guardar el shape de salida
##        file = QFileDialog.getOpenFileName(self.dlg, 'Archivo shape de salida' \
##        ,'', filter='*.csv')
##
##        file = QFileDialog.getExistingDirectory(self.dlg, 'Working Path' \
##                ,'', filter='*.csv')

        file = QFileDialog.getExistingDirectory(self.dlg,
         "Choose Or Create Directory","C:\\",
         QFileDialog.DontResolveSymlinks | QFileDialog.ReadOnly);
        self.dlg.lEIfile.setText(file)
        self.ruta_salida=self.dlg.lEIfile.text()  # set the workspace

    def csvtoShape(self):
        fileRoute = self.dlg.lEIfile.text()
        uri = "file:///"+fileRoute+ \
        "?delimiter=%s&crs=epsg:4326&xField=%s&yField=%s" % (";", "X", "Y")
        lyr = QgsVectorLayer(uri, 'New CSV','delimitedtext')
        QgsMapLayerRegistry.instance().addMapLayer(lyr)
        QMessageBox.information(self.dlg, "Error", fileRoute)

    def csv_to_shape(self):
         capa_csv = self.dlg.mcb_lista_csv.currentLayer()
         pvr = capa_csv.dataProvider()
         ruta_capa = pvr.dataSourceUri().split("|")[0]
         ruta_exporta = self.ruta_salida
         uri = "file:///"+ruta_capa+ \
         "?delimiter=%s&crs=epsg:4326&xField=%s&yField=%s" % (";", "x", "y")
         lyr_capa_csv = QgsVectorLayer(uri, 'Delitosx','delimitedtext')
         self.exporta_capa(lyr_capa_csv,ruta_exporta) # funciona exporta a shape
         print "hola"

    def exporta_capa(self,capa,ruta_wokspace):# esta funcion convierte un layer visrtual en un shape en un directoriuo dado
        dest_crs = QgsCoordinateReferenceSystem(3116)
        QgsVectorFileWriter.writeAsVectorFormat(capa,ruta_wokspace+"\\"+capa.name()+".shp", "utf-8", dest_crs, "ESRI Shapefile")
        capa_shape = QgsVectorLayer(ruta_wokspace+"\\"+capa.name()+".shp", capa.name() ,"ogr")
        capa.commitChanges()
        QgsMapLayerRegistry.instance().addMapLayer(capa_shape)
        return capa_shape

    def layerTomemory(self, ruta, nombre):
        layer = self.iface.addVectorLayer(ruta, "layer name you like", "memory")

##        lyr = QgsVectorLayer(ruta,nombre, "memory")
##        QgsMapLayerRegistry.instance().addMapLayers([lyr])
##        QgsMapLayerRegistry.instance().addMapLayer(lyr)


    def calc_radio(self):
        distancias=[]
        pointlayer = self.iface.activeLayer()
        provider = pointlayer.dataProvider()

        spIndex = QgsSpatialIndex() #create spatial index object

        feat = QgsFeature()
        fit = provider.getFeatures() #gets all features in layer

        # insert features to index
        while fit.nextFeature(feat):
            spIndex.insertFeature(feat)

        #pt = QgsPoint(-0.00062201,0.00001746)
        for fe in pointlayer.getFeatures():
            pt =fe.geometry().asPoint()
            nearestIds = spIndex.nearestNeighbor(pt,2)
            featureId = nearestIds[1]
            fit2 = pointlayer.getFeatures(QgsFeatureRequest().setFilterFid(featureId))
            ftr = QgsFeature()
            fit2.nextFeature(ftr)
            d = QgsDistanceArea()
            m = d.measureLine(pt,ftr.geometry().asPoint())
            distancias.append(m)
        print "el promedio de las distancias es : %s m" %(str(sum(distancias)/len(distancias)))

    def kernel_gausiano(self):
        layer=self.iface.activeLayer()
        ruta=self.layer_path()
        extent=self.get_extent()
        processing.runalg("saga:kerneldensityestimation",ruta,"Delito",300,1,extent,100,self.ruta_salida+layer.name()+".tif")
        rasterLyr = QgsRasterLayer(self.ruta_salida+layer.name()+".tif", "Ker_"+layer.name())
        QgsMapLayerRegistry.instance().addMapLayers([rasterLyr])

##        self.getextent()

    def layer_path(self):
        layer = self.iface.activeLayer()
        pvr = layer.dataProvider()
        layer_path = pvr.dataSourceUri().split("|")[0]
        return layerpath

    def get_extent(self):
        layer=self.iface.activeLayer()
        e = layer.extent()
        xmin=str(e.xMinimum())
        xmax=str(e.xMaximum())
        ymin=str(e.yMinimum())
        ymax=str(e.yMaximum())
        extent=str(xmin+","+xmax+","+ymin+","+ymax)
        return extent

    def export_by_date(self):
        anios=["2010","2011","2012","2013"]
        layer=self.iface.activeLayer()
        ruta_exporta=self.ruta_salida
        for an in anios:
            layer_anio=self.exporta_features(layer,"PERIODO",an)
            self.exporta_capa(layer_anio,ruta_exporta)
            del layer_anio

    def exporta_features(self,layer_origen,campo,dato):
        #captura el sistema de coordenadas del primer layer que este cargado en el qgis
        layers = self.iface.legendInterface().layers()
        coord_layer = layers[0].crs()
        layer_crs = coord_layer.authid()
        coordenadas = "Point?crs=%s" % layer_crs
        layer_virtual = QgsVectorLayer(coordenadas, dato, "memory")# crea un layer virtual asignando el sistema de coordenadas del primer layer que este cargado en el qgis
        layer_virtual.startEditing()#comienza la edicion
        layer_virtual.dataProvider().addAttributes(list(layer_origen.dataProvider().fields()))#le añade los campos del layer origen
##        features_origen=layer_origen.dataProvider().getFeatures(QgsFeatureRequest().setFilterExpression('"'+campo+'" = '+"'"+dato+"'"))# trae las features que solo cumplen las condiciones del filtro
        features_origen=layer_origen.dataProvider().getFeatures(QgsFeatureRequest().setFilterExpression('"'+campo+'" = '+dato))# trae las features que solo cumplen las condiciones del filtro
        for feature in features_origen:# almacena las features capturadas en el layer virtual
            layer_virtual.dataProvider().addFeatures([feature])
        #guarda los cambios
        layer_virtual.commitChanges()
        layer_virtual.updateFields()
        layer_virtual.updateExtents()
        return layer_virtual # devuelve el layer virtual

    def list_years(self):
        try:
            #captura el layer activo
            layer=self.iface.activeLayer()
            if layer:

                n_capa=self.iface.activeLayer().name()
                self.dlg.text_capa_activa.setText(n_capa)
                if layer.type() == QgsMapLayer.VectorLayer:  # verifica si es vectorial y el tipo de geometria
                    #captura las features
                    fea=layer.getFeatures()
                    for featurex in fea:
                        attributos=featurex.attributes()
##                    num_atributos=len(attributos)
##                    self.dlg.text_numatt.setText(str(num_atributos))
                else:
                    QMessageBox.information(self.dlg, "Error", "El layer no es vectorial")
        except:
            QMessageBox.information(self.dlg, "Error", "Por favor cargue por lo menos una capa vectorial")

    def load_fields(self):# funci{on que cambias los atributos al cambiar de layer
        layer= self.dlg.mcb_lista_csv.currentLayer ()
        self.dlg.mfcb_fields.setLayer(layer)

    def get_years_values(self):# llena el combo con los valores del atributo seleccionado
        layer=self.dlg.mcb_lista_csv.currentLayer()
        field=self.dlg.mfcb_fields.currentField()
        all_values = []
        uniq_values = []
        features= layer.getFeatures()
        for feature in features:
            all_values.append(feature[field])
        uniq_values=self.uniq(all_values)
        uniq_values.sort() # para que la lista salga en orden
        print uniq_values


    def uniq(self,inlist): # funcion que devuelve los valores unicos en una lista
        # preservando el orden
        uniques = []
        for item in inlist:
            if item not in uniques:
                uniques.append(item)
        return uniques






##        for a in uniq_values:
##            self.dlg.cBValues.addItem(str(a))
##        distancias=[]
##        distancias_minimas=[]
##        mapa = self.iface.mapCanvas()
##        layer= mapa.currentLayer()
##        medidor = QgsDistanceArea() # crea el objeto de medicion
##        for f1 in layer.getFeatures(): # para todos los estudientes
##             for f2 in layer.getFeatures(): # para todos los colegios
##                 m = medidor.measureLine(f1.geometry().asPoint(),f2.geometry().asPoint()) # calcula la distancia entre el colegio y el estudiante
##                 m = medidor.convertMeasurement(m, 2, 0, False) # la convierte en metros a partir de grados decimales
##                 m = m[0] # obtiene solo el valor de la distancia porque viene así (4545,0)
##                 distancias.append(m)
##             distancias_minimas.append(min(distancias))
##        print distancias_minimas







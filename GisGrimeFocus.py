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
# needed for raster calculator
from qgis.analysis import QgsRasterCalculator, QgsRasterCalculatorEntry
from math import *  # needed for operations in raster calculator
import gistfile1 as jenks  # imports the module for do the jenks class splits
#  obtained from https://gist.github.com/drewda/1299198


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
        self.output_path = ""
        self.years = []
        self.imported_layer = ""
        self.years_layers =[]
        self.raster_years_layers =[]
        self.raster_layer_ws=""
        self.vectorized_sum = ""
        self.crime_distances = []
        self.crime_sd = []
        self.crime_radios = []
        self.added_layers = []
        self.progressValue=0


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
        # set the default crs system
        dest_crs =self.dlg.mpsw_crs.setCrs(QgsCoordinateReferenceSystem(3116))
        # funcion que guarda la ruta del archivo de salida en el text
        # correspondiente
        self.dlg.pBSearchFile.clicked.connect(self.readInputData)

        #funcionque conecta al boton con la funcion de convertir el scv en shape
        #  y cargarlo
        self.dlg.pBImport.clicked.connect(self.validations)

        self.dlg.mcb_lista_csv.layerChanged.connect(self.load_fields)
        self.dlg.pb_clean.clicked.connect(self.clean)

        # funcion que habilita el radio buton de numero de features al seleccionar
        # el cuadro de cifras
        self.dlg.dsb_bandwith.valueChanged.connect(self.radio_custom_click)



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

        file = QFileDialog.getExistingDirectory(self.dlg,
         "Escoge un folder","C:\\",
         QFileDialog.DontResolveSymlinks);
        self.dlg.lEIfile.setText(file)
        self.output_path=self.dlg.lEIfile.text()  # set the workspace

    def csv_to_shape(self):
         capa_csv = self.dlg.mcb_lista_csv.currentLayer()
         pvr = capa_csv.dataProvider()
         ruta_capa = pvr.dataSourceUri().split("|")[0]
         self.output_path=self.dlg.lEIfile.text()  # set the workspace
         ruta_exporta = self.dlg.lEIfile.text()
         uri = "file:///"+ruta_capa+ \
         "?delimiter=%s&crs=epsg:4326&xField=%s&yField=%s" % (";", "x", "y")
         lyr_capa_csv = QgsVectorLayer(uri, 'Delitosx','delimitedtext')
         self.imported_layer = self.layer_export(lyr_capa_csv,ruta_exporta) # funciona exporta a shape


    def layer_export(self,capa,ruta_wokspace):# esta funcion convierte un layer visrtual en un shape en un directoriuo dado
        dest_crs =self.dlg.mpsw_crs.crs ()
        QgsVectorFileWriter.writeAsVectorFormat(capa,ruta_wokspace+"\\"+capa.name()+".shp", "utf-8", dest_crs, "ESRI Shapefile")
        capa_shape = QgsVectorLayer(ruta_wokspace+"\\"+capa.name()+".shp", capa.name() ,"ogr")
        capa.commitChanges()
        QgsMapLayerRegistry.instance().addMapLayer(capa_shape)
        return capa_shape

    def calc_radio(self,layer):
        distances=[]
        pointlayer = layer
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
            distances.append(m)
        self.crime_distances.append(self.mean(distances))
        self.crime_sd.append(self.pstdev(distances))
        return self.pstdev(distances) ,self.mean(distances)


    def kernel_gausiano(self):
        year_count = len(self.years_layers)
        for i in range(year_count):

            layer = self.years_layers[i]
            sd,avr = self.calc_radio(layer)

            if self.dlg.rb_default_bw.isChecked() is True:
                radio =avr + 1*sd
            else:
                radio =self.dlg.dsb_bandwith.value()
            print radio
            cell_size = self.dlg.dsb_cellsize.value()
            ruta = self.layer_path(layer)
            extent = self.get_extent()
            processing.runalg("saga:kerneldensityestimation",ruta,"Delito",radio,1,extent,cell_size,self.output_path+'//'+layer.name()+".tif")
            rasterLyr = QgsRasterLayer(self.output_path+'//'+layer.name()+".tif", "Ker_"+layer.name())
            self.raster_years_layers.append(rasterLyr)
            QgsMapLayerRegistry.instance().addMapLayers([rasterLyr])
            self.increment(5)


    def layer_path(self,layer):
        pvr = layer.dataProvider()
        layer_path = pvr.dataSourceUri().split("|")[0]
        return layer_path

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
        self.years = self.get_years_values()
        anios=self.years
        layer = self.imported_layer
        ruta_exporta = self.output_path
        for an in anios:
            layer_anio = self.feature_export(layer,"PERIODO",an,"")
            self.years_layers.append(self.layer_export(layer_anio,ruta_exporta))
            del layer_anio

    def feature_export(self,layer_origen,campo,dato,expression):
        #captura el sistema de coordenadas del primer layer que este cargado en el qgis
        layers = self.iface.legendInterface().layers()
        coord_layer = layers[0].crs()
        layer_crs = coord_layer.authid()
        if layers[0].geometryType() == QGis.Point:
            coordenadas = "Point?crs=%s" % layer_crs
        elif layers[0].geometryType() == QGis.Polygon:
            coordenadas = "Polygon?crs=%s" % layer_crs

        if expression == "":
            layer_virtual = QgsVectorLayer(coordenadas, dato, "memory")# crea un layer virtual asignando el sistema de coordenadas del primer layer que este cargado en el qgis
            layer_virtual.startEditing()#comienza la edicion
            layer_virtual.dataProvider().addAttributes(list(layer_origen.dataProvider().fields()))#le añade los campos del layer origen
            features_origen=layer_origen.dataProvider().getFeatures(QgsFeatureRequest().setFilterExpression('"'+campo+'" = '+dato))# trae las features que solo cumplen las condiciones del filtro
        else:
            layer_virtual = QgsVectorLayer(coordenadas, "DN_%s"%str(dato), "memory")# crea un layer virtual asignando el sistema de coordenadas del primer layer que este cargado en el qgis
            layer_virtual.startEditing()#comienza la edicion
            layer_virtual.dataProvider().addAttributes(list(layer_origen.dataProvider().fields()))#le añade los campos del layer origen
            features_origen=layer_origen.dataProvider().getFeatures(QgsFeatureRequest().setFilterExpression('"'+campo+'" >= '+str(dato)))# trae las features que solo cumplen las condiciones del filtro

        for feature in features_origen:# almacena las features capturadas en el layer virtual
            layer_virtual.dataProvider().addFeatures([feature])
        #guarda los cambios
        layer_virtual.commitChanges()
        layer_virtual.updateFields()
        layer_virtual.updateExtents()
        return layer_virtual # devuelve el layer virtual


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
        return uniq_values


    def uniq(self,inlist): # funcion que devuelve los valores unicos en una lista
        # preservando el orden
        uniques = []
        for item in inlist:
            if item not in uniques:
                uniques.append(item)
        return uniques


    def mean(self,data):
        """Return the sample arithmetic mean of data."""
        n = len(data)
        if n < 1:
            raise ValueError('mean requires at least one data point')
        return sum(data)/n # in Python 2 use sum(data)/float(n)


    def _ss(self,data):
        """Return sum of square deviations of sequence data."""
        c = self.mean(data)
        ss = sum((x-c)**2 for x in data)
        return ss

    def pstdev(self,data):
        """Calculates the population standard deviation."""
        n = len(data)
        if n < 2:
                raise ValueError('variance requires at least two data points')
        ss = self._ss(data)
        pvar = ss/n # the population variance
        return pvar**0.5

    def radio_custom_click(self):
        #activa el radio button de la seleccion aleatoria por numero de elementos al cambiar los valores del spinbox
        self.dlg.rb_custom_bw.toggle()

    def get_natural_breaks(self,data,num_class):
        class_intervals=jenks.getJenksBreaks(data,num_class)
        return class_intervals

    def weighted_sum(self):
        entries = []  # stores the enties for the rascalc operation
        instruccions=""
        numbers=[x for x in xrange(0,100)]
        numrasters = len(self.raster_years_layers)
        factor =[1 - 0.2* x for x in xrange(0,numrasters)]
        factor.sort()
        items= ['(layer%s@1)'%(str(x)) for x in xrange(1,numrasters+1)]
        sum_op = [items[x]+"*"+str(factor[x]) for x in xrange(0,len(factor))]
        expresion = " + ".join(sum_op)

        for x in xrange(1,numrasters+1):
            instruccions+='layer%s = QgsRasterCalculatorEntry();'%(str(x))
            instruccions+="layer%s.ref = 'layer%s@1';"%(str(x),str(x))
            instruccions+='layer%s.raster = self.raster_years_layers[%d];'%(str(x),x-1)
            instruccions+='layer%s.bandNumber = 1;'%(str(x))
            if x==numrasters:
                instruccions+='entries.append( layer%s )'%(str(x))
            else:
                instruccions+='entries.append( layer%s );'%(str(x))
        exec(instruccions)
        print expresion
        calc = QgsRasterCalculator(expresion,
                            self.output_path+'\\'+'suma_ponderada.tif',
                            'GTiff',
                            self.imported_layer.extent(),
                            self.raster_years_layers[0].width(),
                            self.raster_years_layers[0].height(),
                            entries )

        calc.processCalculation()
        rasterLyr = QgsRasterLayer(self.output_path+'\\'+'suma_ponderada.tif', "suma_ponderada")
        self.raster_layer_ws=self.output_path+'\\'+'suma_ponderada.tif'
        QgsMapLayerRegistry.instance().addMapLayers([rasterLyr])

    def vectorize(self):
        processing.runalg("gdalogr:polygonize",self.raster_layer_ws,"DN",self.output_path+'\\'+'suma_vectorizada.shp')
        self.vectorized_sum = self.output_path+'\\'+'suma_vectorizada.shp'
        capa_shape = QgsVectorLayer(self.vectorized_sum, "suma_vectorizada" ,"ogr")
        QgsMapLayerRegistry.instance().addMapLayers([capa_shape])
        return capa_shape

    def select_critics(self,layer):
        dn_values = []
        for f in layer.getFeatures():
	      dn_values.append(f["DN"])
        jenks_breaks = self.get_natural_breaks(dn_values,5)
        expresion = ""
        layer_select1 = self.feature_export(layer,"DN",str(jenks_breaks[2:][0]),"y")
        QgsMapLayerRegistry.instance().addMapLayers([layer_select1])
        return layer_select1

    def increment(self, value):
        self.progressValue+=value
        self.dlg.progressBar.setValue(self.progressValue)

    def clean(self):
        self.dlg.mpsw_crs.setCrs(QgsCoordinateReferenceSystem(3116))
        self.dlg.lEIfile.clear()
        self.dlg.mcb_lista_csv.clear()
        self.dlg.mfcb_fields.clear()
        self.dlg.dsb_bandwith.setValue(10)
        self.dlg.dsb_cellsize.setValue(10)
        self.progressValue=0
        self.dlg.progressBar.setValue(0)

    def validations(self):
        self.texto_mensajes="Por favor verifique los siguientes mensajes: \n"
        if not os.path.isdir(str(self.dlg.lEIfile.text())):
            self.texto_mensajes+=' Por favor seleeccione un folder de salida existente \n'

        if self.texto_mensajes!="Por favor verifique los siguientes mensajes: \n":
            QMessageBox.information(self.dlg, "Error", self.texto_mensajes)
        else:
             # si todo esta bien ejecuta la funcion principal
             self.main()
        self.texto_mensajes=""



    def main(self):
        self.progressValue=0
        self.dlg.progressBar.setValue(0)
        self.dlg.lbl_progress.setText("Convirtiendo a shapefile")
        self.csv_to_shape()  # import the csvfile stores it and export to shp
        self.increment(10)
        self.dlg.lbl_progress.setText("Exportando cada fecha a shapefile")
        self.export_by_date()  # export a shp for every year
        self.increment(10)
        self.dlg.lbl_progress.setText("Calculando el kernel gausiano")
        self.kernel_gausiano()

        self.dlg.lbl_progress.setText("Calculando la suma ponderada")
        self.weighted_sum()
        self.increment(10)
        self.dlg.lbl_progress.setText("Vectorizando")
        layer_sel = self.vectorize()
        layer_critics = self.select_critics(layer_sel)
        layer_critics_shape = self.layer_export(layer_critics,self.output_path)
        self.dlg.lbl_progress.setText("Ejecutando el dissolve")
        processing.runalg("saga:polygondissolveallpolygons",self.layer_path(layer_critics_shape),False,self.output_path+'//'+layer_critics.name()+"_diss.shp")
        path_layer_diss = self.output_path+'//'+layer_critics.name()+"_diss.shp"
        capa_dissolved = QgsVectorLayer(path_layer_diss, "zonas_disueltas" ,"ogr")
        QgsMapLayerRegistry.instance().addMapLayers([capa_dissolved])
        self.increment(10)

        avr_avr = self.mean(self.crime_distances)
        avr_std_desv = self.mean(self.crime_sd)
        buffer_radio = avr_avr + avr_std_desv
        self.dlg.lbl_progress.setText("Calculando el buffer")
        processing.runalg("saga:shapesbufferfixeddistance",self.layer_path(capa_dissolved),buffer_radio,1,5,True,False,self.output_path+'//'+layer_critics.name()+"_buff.shp")
        path_layer_buff = self.output_path+'//'+layer_critics.name()+"_buff.shp"
        capa_buff = QgsVectorLayer(path_layer_buff, "zonas_buffer" ,"ogr")
        QgsMapLayerRegistry.instance().addMapLayers([capa_buff])
        self.increment(10)

        self.dlg.lbl_progress.setText("Convirtiendo a multipartes")
        processing.runalg("qgis:multiparttosingleparts",path_layer_buff,self.output_path+'//'+layer_critics.name()+"_multi.shp")
        path_layer_multi = self.output_path+'//'+layer_critics.name()+"_multi.shp"
        capa_multi = QgsVectorLayer(path_layer_multi, "zonas_disueltas_buffer" ,"ogr")
        QgsMapLayerRegistry.instance().addMapLayers([capa_multi])
        self.increment(10)
        self.dlg.lbl_progress.setText("Calculando el numero de casos por area")
        processing.runalg("qgis:countpointsinpolygon",path_layer_multi,self.layer_path(self.years_layers[len(self.years_layers)-1]),"NUMPOINTS",self.output_path+'//'+"zonas_criticas.shp")
        path_layer_critic = self.output_path+'//'+"zonas_criticas.shp"
        capa_critica = QgsVectorLayer(path_layer_critic, "Zonas_Criticas" ,"ogr")
        QgsMapLayerRegistry.instance().addMapLayers([capa_critica])
        self.increment(10)
        self.dlg.lbl_progress.setText("Proceso finalizado con exito")
        self.increment(10)



    if __name__ == '__main__':
        main()




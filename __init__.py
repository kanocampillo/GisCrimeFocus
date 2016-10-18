# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GisGrimeFocus
                                 A QGIS plugin
 ass
                             -------------------
        begin                : 2016-10-02
        copyright            : (C) 2016 by as
        email                : s
        git sha              : $Format:%H$
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load GisGrimeFocus class from file GisGrimeFocus.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .GisGrimeFocus import GisGrimeFocus
    return GisGrimeFocus(iface)

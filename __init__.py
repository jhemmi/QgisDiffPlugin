# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Diff
                                 A QGIS plugin
 Diff between a vector and a text file
                             -------------------
        begin                : 2015-06-24
        copyright            : (C) 2015 by jhemmi.eu
        email                : jean@jhemmi.eu
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
    """Load Diff class from file Diff.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .diff import Diff
    return Diff(iface)

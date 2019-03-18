# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2014 Akretion (http://www.akretion.com).
#   @author Sylvain LE GAL (https://twitter.com/legalsylvain)
#   @author Sébastien BEAU <sebastien.beau@akretion.com>
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

import commands
import platform
import pkg_resources
import os

from flask import render_template
from flask_cors import cross_origin
from flask.ext.babel import gettext as _

from pywebdriver import app, drivers


@app.route("/", methods=['GET'])
@app.route('/index.html', methods=['GET'])
@cross_origin()
def index():
    return render_template('index.html')


@app.route('/status.html', methods=['GET'])
@cross_origin()
def status():
    drivers_info = {}

    for driver in drivers:
        tmp = drivers[driver].get_vendor_product()
        if tmp:
            image = 'static/images/' + tmp + '.png'
        else:
            image = None
        drivers_info[driver] = {
            'state': drivers[driver].get_status(),
            'image': image,
        }
    return render_template('status.html', drivers_info=drivers_info)


@app.route('/usb_devices.html', methods=['GET'])
@cross_origin()
def usb_devices():
    str_devices = commands.getoutput("lsusb").split('\n')
    devices = []
    for device in str_devices:
        devices.append({
            'bus': device.split(": ID ")[0].split(" ")[1],
            'device': device.split(": ID ")[0].split(" ")[3],
            'id': device.split(": ID ")[1][:9],
            'description': device.split(": ID ")[1][10:],
        })
    return render_template('usb_devices.html', devices=devices)


@app.route('/system.html', methods=['GET'])
@cross_origin()
def system():
    system_info = []
    system_info.append({
        'name': _('OS - System'), 'value': platform.system()})
    system_info.append({
        'name': _('OS - Distribution'),
        'value': platform.linux_distribution()})
    system_info.append({
        'name': _('OS - Release'), 'value': platform.release()})
    system_info.append({
        'name': _('OS - Version'), 'value': platform.version()})
    system_info.append({
        'name': _('Machine'), 'value': platform.machine()})
    system_info.append({
        'name': _('Python Version'), 'value': platform.python_version()})
    installed_python_packages = [d for d in pkg_resources.working_set]
    installed_python_packages = sorted(
        installed_python_packages, key=lambda package: package.key)
    return render_template(
        'system.html',
        system_info=system_info,
        installed_python_packages=installed_python_packages)


@app.route(
    '/static/images/<path:path>',
    methods=['POST', 'GET', 'PUT', 'OPTIONS'])
def image_html(path=None):
    return app.send_static_file(os.path.join('images/', path))

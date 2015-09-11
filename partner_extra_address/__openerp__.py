# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Therp BV <http://therp.nl>.
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Partner extra address',
    'description': """
Extra addresses can be added for a company to res_partner. When you have
multiple invoice or delivery or whatever type addresses, you should be able
to specify the default, that also should be shown first in selection lists.

The module also offers a compact view that can be used from views that
have a many2one field to res.partner.

Example for an extra sender_address from sale_order:

Contributors
============
Ronald Portier <ronald@therp.nl>

""",
    'version': '8.0.0',
    'author': 'Therp BV',
    'maintainer': 'OCA, Therp BV',
    'category': 'Extra Tools',
    'website': 'http://www.therp.nl',
    'depends': ['base'],
    'data': [
        'view/res_partner.xml',
    ],
    'auto_install': False,
    'installable': True,
}

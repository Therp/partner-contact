# -*- coding: utf-8 -*-
"""Extend res.partner model to set default address per type."""
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
from openerp import api, models, fields


class Partner(models.Model):
    """Extend res.partner model to set default address per type."""
    _inherit = 'res.partner'

    def _compute_vals(self, vals):
        """Compute vals for create and write"""
        
        def get_val(field, vals, record):
            return field in vals and vals[field] or record[field]

        # Make sure we have only one default per type
        for record in self:
            if not get_val('active', vals, record):
                vals['type_default'] = False  # inactive can not be default
            elif get_val('type_default', vals, record):
                parent_id = get_val('parent_id', vals, record)
                if parent_id:
                    type = get_val('type', vals, record)
                    # Find all records that might need to be reset
                    reset_partners = self.search([
                        ('parent_id', '=', parent_id),
                        ('type', '=', type),
                        ('type_default', '=', True),
                    ])
                    for no_longer_default in reset_partners:
                        no_longer_default.write({'type_default': False})

    @api.model
    def create(self, vals):
        """Call _compute_vals from create."""
        self._compute_vals(vals)
        return super(Partner, self).create(vals)

    @api.multi
    def write(self, vals):
        """Call _compute_vals from write."""
        self._compute_vals(vals)
        return super(Partner, self).write(vals)
    
    type_default = fields.Boolean(string='Default for address type')

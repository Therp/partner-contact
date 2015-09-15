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

        def get_val(field, vals, record, m2o=False):
            """Value from screen or from database."""
            if field in vals:
                return vals[field]  # Might be False for boolean
            elif m2o:
                return record[field].id
            else:
                return record[field]

        # Make sure we have only one default per type
        for record in self:
            if not get_val('active', vals, record):
                vals['type_default'] = False  # inactive can not be default
            elif get_val('type_default', vals, record):
                parent_id = get_val('parent_id', vals, record, m2o=True)
                if parent_id:
                    type = get_val('type', vals, record)
                    # Find all records that might need to be reset
                    reset_partners = self.search([
                        ('id', '!=', record.id),
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

    @api.multi
    def address_get(self, adr_pref=None):
        """Preprocess standard address_get to return default address for
        the address types specified in adr_pref, that have a default for the
        partners indicated. This has nothing to do with the global default
        address, which is rather the fallback address if an address of the
        desired type can not be found."""
        parent_id = self.parent_id or self.id
        defaults_found = {}
        if parent_id:  # Default makes no sense otherwise
            adr_pref = set(adr_pref or [])
            for type in adr_pref:
                default_address = self.search([
                    ('parent_id', '=', parent_id),
                    ('type', '=', type),
                    ('type_default', '=', True),
                ])
                if default_address:
                    defaults_found[type] = default_address.id
        result = super(Partner, self).address_get(adr_pref=adr_pref)
        result.update(defaults_found)
        return result

    # ==== Start field definitions
    type_default = fields.Boolean(
        string='Default for address type',
        default=False,
    )
    # ====== End field definitions

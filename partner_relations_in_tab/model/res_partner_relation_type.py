# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    This module copyright (C) 2014 Therp BV (<http://therp.nl>).
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
from odoo import api, fields, models


class ResPartnerRelationType(models.Model):
    _inherit = 'res.partner.relation.type'

    own_tab_left = fields.Boolean('Show in own tab', default=False)
    own_tab_right = fields.Boolean('Show in own tab', default=False)

    def _update_res_partner_fields(self):
        field_name_prefix = 'relation_ids_own_tab_'
        field_name_format = field_name_prefix + '%s_%s'
        res_partner = self.env['res.partner']
        for field_name in res_partner._fields.copy():
            if field_name.startswith(field_name_prefix):
                del res_partner._fields[field_name]

        def add_field(relation, inverse):
            field = fields.One2many(
                'res.partner.relation',
                '%s_partner_id' % ('left' if not inverse else 'right'),
                string=relation['name' if not inverse else 'name_inverse'],
                domain=[('type_id', '=', relation.id),
                        '|',
                        ('active', '=', True),
                        ('active', '=', False)])
            field_name = field_name_format % (
                relation.id,
                'left' if not inverse else 'right')
            res_partner._add_field(field_name, field)

        for relation in self.sudo().search(
                    ['|',
                     ('own_tab_left', '=', True),
                     ('own_tab_right', '=', True),
                    ]):
            if relation.own_tab_left:
                add_field(relation, False)
            if relation.own_tab_right:
                add_field(relation, True)

    def _register_hook(self):
        self._update_res_partner_fields()

    @api.model
    def create(self, vals):
        result = super(ResPartnerRelationType, self).create(vals)
        if vals.get('own_tab_left') or vals.get('own_tab_right'):
            self._update_res_partner_fields()
        return result

    @api.multi
    def write(self, vals):
        result = super(ResPartnerRelationType, self).write(vals)
        for record in self:
            if 'own_tab_left' in vals or 'own_tab_right' in vals:
                record._update_res_partner_fields()
        return result

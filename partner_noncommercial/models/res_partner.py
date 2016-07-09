# -*- coding: utf-8 -*-
# © 2015-2016 Therp BV (http://therp.nl).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from openerp import api, fields, models


class ResPartner(models.Model):
    """Override designation 'Company' with more general 'Organisation'."""
    _inherit = 'res.partner'

    is_company = fields.Boolean(
        string='Is an Organisation',
        help="Check if a relation is an organisation,"
             " otherwise it is a person"
    )
    company_type = fields.Selection(
        selection_add=[
            ('ngo', 'Non Governmental Organisation'),
            ('gov', 'Government body'),
            ('edu', 'Educational institution'),
        ],
        string='Organisation Type',
        help="This is officialy a technical field in Odoo 9.0. However it is"
             " very usefull to distinguish different kinds of organisations."
    )

    @api.multi
    def on_change_company_type(self, company_type):
        """Any partner that is not a person, is an organisation of some kind.

        In standard Odoo all organisations are supposed to be companies, but
        of course that is not the case for government organisaties, ngo's,
        political parties etc.
        """
        return {'value': {'is_company': company_type != 'person'}}

# Copyright 2021 Akretion France
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    same_email_partner_id = fields.Many2one(
        "res.partner",
        compute="_compute_same_email_partner_id",
        string="Partner with same e-mail",
        compute_sudo=True,
    )

    @api.depends(lambda x: x._get_same_email_depends())
    def _compute_same_email_partner_id(self):
        empty_recordset = self.env[self._name]
        for partner in self:
            partner.same_email_partner_id = (
                partner._find_same_email_partner() if partner.email else empty_recordset
            )

    def _find_same_email_partner(self):
        """Find one partner with the same e-mail."""
        self.ensure_one()
        domain = self._get_same_email_domain()
        return self.with_context(active_test=False).search(domain, limit=1)

    @api.model
    def _get_same_email_depends(self):
        """Return the fields on which same_email_partner_id depends.

        Return the fields used in _get_same_email_domain function.
        """
        return ["email", "company_id"]

    def _get_same_email_domain(self):
        """Return domain to find partners with same e-mail."""
        self.ensure_one()
        email_value = (self.email or "").strip()
        domain = [("email", "=ilike", email_value)]
        if self.company_id:
            domain += [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", self.company_id.id),
            ]
        self_id = self._origin.id
        if self_id:
            domain.append(("id", "!=", self_id))
        return domain

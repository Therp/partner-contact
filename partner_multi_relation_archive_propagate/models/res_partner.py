# Copyright 2025 Therp BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import _, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    def _has_propagating_relations(self):
        """Return True if partner has at least one relation with propagate_archive=True."""
        self.ensure_one()
        Relation = self.env["res.partner.relation"].sudo()
        return bool(
            Relation.search_count(
                [
                    "|",
                    ("left_partner_id", "=", self.id),
                    ("right_partner_id", "=", self.id),
                    ("type_id.propagate_archive", "=", True),
                ]
            )
        )

    def _compute_show_prop_wizard_button(self):
        # Keep original logic (children) and extend for relation-based propagation.
        res = super()._compute_show_prop_wizard_button()
        for partner in self:
            if partner.is_company and partner._has_propagating_relations():
                partner.show_prop_wizard_button = True
        return res

    def _get_related_partners_for_archive_propagation(self):
        """Return partners related to self via types with propagate_archive."""
        self.ensure_one()
        Relation = self.env["res.partner.relation"].sudo()
        relations = Relation.search(
            [
                "|",
                ("left_partner_id", "=", self.id),
                ("right_partner_id", "=", self.id),
                ("type_id.propagate_archive", "=", True),
            ]
        )
        related = self.env["res.partner"]
        for rel in relations:
            if rel.left_partner_id == self:
                other = rel.right_partner_id
            else:
                other = rel.left_partner_id
            related |= other
        return related

    def _archive_propagate_wizard(self):
        """
        Only organisational partners (is_company = True) propagate via relations.
        -On archive: related partners (via relation types with propagate_archive = True)
          are archived when possible and flagged with propagated_from_id = source company.
        """
        res = super()._archive_propagate_wizard()
        self._archive_multi_relation()
        return res

    def _archive_propagate_external(self):
        res = super()._archive_propagate_external()
        self._archive_multi_relation()
        return res

    def _archive_multi_relation(self):
        companies = self.filtered(lambda p: p.is_company)
        if not companies:
            return
        for company in companies:
            related = company._get_related_partners_for_archive_propagation().filtered(
                lambda p: p.active
            )
            if not related:
                continue
            archivable, unarchivable = related._split_archivable_unarchivable_user()
            archivable.write(
                {
                    "active": False,
                    "propagated_from_id": company.id,
                }
            )
            company._notify_skipped_partners(unarchivable)

    def action_archive_with_contacts(self):
        """Show wizard also for company partners with propagating relations"""
        self.ensure_one()
        # Check if it would archive immediately.
        # If it is a company, would archive immediately,
        # and has relation contacts, then
        # throw wizard
        descendants = self._get_descendants().filtered(lambda p: p.active)
        contact_desc = descendants.filtered(lambda p: p.type == "contact")
        if not contact_desc and self.is_company:
            related_contacts = (
                self._get_related_partners_for_archive_propagation().filtered(
                    lambda p: p.active and p.type == "contact"
                )
            )
            if related_contacts:
                (
                    archivable,
                    unarchivable,
                ) = related_contacts._split_archivable_unarchivable_user()
                wiz = self.env["res.partner.archive.propagate.wizard"].create(
                    {
                        "partner_id": self.id,
                        "line_ids": [(0, 0, {"partner_id": p.id}) for p in archivable],
                    }
                )
                self._notify_skipped_partners(unarchivable)
                return {
                    "type": "ir.actions.act_window",
                    "name": _("Archive Contacts"),
                    "res_model": "res.partner.archive.propagate.wizard",
                    "view_mode": "form",
                    "target": "new",
                    "res_id": wiz.id,
                }
        # default to hierarchical wizard or immediate archive
        return super().action_archive_with_contacts()

# Copyright 2025 Therp BV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests.common import TransactionCase


class TestPartnerMultiRelationArchivePropagate(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(su=True)
        Partners = cls.env["res.partner"]
        RelationType = cls.env["res.partner.relation.type"]
        Relation = cls.env["res.partner.relation"]
        # Organisation and two related partners
        cls.org = Partners.create({"name": "Org", "is_company": True})
        cls.rel1 = Partners.create({"name": "Rel1"})
        cls.rel2 = Partners.create({"name": "Rel2"})
        # Relation type with propagation enabled
        cls.rel_type = RelationType.create(
            {
                "name": "Org -> Rel",
                "name_inverse": "Rel -> Org",
                "propagate_archive": True,
            }
        )
        # Create relations from org to rel1 and rel2
        Relation.create(
            {
                "type_id": cls.rel_type.id,
                "left_partner_id": cls.org.id,
                "right_partner_id": cls.rel1.id,
            }
        )
        Relation.create(
            {
                "type_id": cls.rel_type.id,
                "left_partner_id": cls.org.id,
                "right_partner_id": cls.rel2.id,
            }
        )

    def _create_active_user_for_partner(self, partner, login):
        """Create an active user linked to a partner."""
        return (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": partner.name,
                    "login": login,
                    "partner_id": partner.id,
                    "email": "amail@mail.com",
                }
            )
        )

    def test_archive_org_archives_related(self):
        """Archiving a company archives related partners via propagate_archive type."""
        # Ensure non-UI propagation is enabled
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("partner_archive_propagate.force_outside_ui", "1")
        # Make rel2 unarchivable by linking an active user
        self._create_active_user_for_partner(self.rel2, "rel2_user")
        before_msgs = len(self.org.message_ids)
        # Archive the company
        self.org.write({"active": False})
        # Org should be inactive
        self.assertFalse(self.org.active)
        # rel1 should be archived and flagged as propagated from org
        self.rel1.invalidate_recordset()
        self.assertFalse(self.rel1.active)
        self.assertEqual(
            self.rel1.propagated_from_id,
            self.org,
            "rel1 should be archived due to org via propagated_from_id",
        )
        # rel2 should remain active and not flagged
        self.rel2.invalidate_recordset()
        self.assertTrue(self.rel2.active)
        self.assertFalse(
            bool(self.rel2.propagated_from_id),
            "rel2 should not be archived nor flagged because of active user",
        )
        # A message should be posted about skipped contacts (rel2)
        self.assertEqual(len(self.org.message_ids), before_msgs + 1)
        msg = self.org.message_ids.sorted("id")[-1]
        self.assertIn("Skipped archiving the following contacts", msg.body)
        self.assertIn(self.rel2.name, msg.body)
        # Reset setting for other tests
        icp.set_param("partner_archive_propagate.force_outside_ui", "0")

    def test_unarchive_org_restores_related(self):
        """Unarchiving a company restores only related partners flagged as propagated."""
        # Prepare state:
        # - org inactive
        # - rel1 archived & flagged from org
        # - rel2 archived but NOT flagged
        self.org.write({"active": False})
        self.rel1.write(
            {
                "active": False,
                "propagated_from_id": self.org.id,
            }
        )
        self.rel2.write(
            {
                "active": False,
                "propagated_from_id": False,
            }
        )
        # Unarchive org
        self.org.write({"active": True})
        # Org is active
        self.assertTrue(self.org.active)
        # rel1 should be unarchived and propagated_from_id cleared
        self.rel1.invalidate_recordset()
        self.assertTrue(self.rel1.active)
        self.assertFalse(
            bool(self.rel1.propagated_from_id),
            "rel1 should be unarchived and flag cleared",
        )
        # rel2 should remain archived and unflagged
        self.rel2.invalidate_recordset()
        self.assertFalse(self.rel2.active)
        self.assertFalse(
            bool(self.rel2.propagated_from_id),
            "rel2 should remain archived and unflagged",
        )

    def test_non_company_does_not_propagate(self):
        """Archiving a non-company with relations must not propagate."""
        person = self.env["res.partner"].create({"name": "Person", "is_company": False})
        # Attach a relation type with propagate_archive
        RelationType = self.env["res.partner.relation.type"]
        Relation = self.env["res.partner.relation"]
        rel_type = RelationType.create(
            {
                "name": "Person -> Rel1",
                "name_inverse": "Rel1 -> Person",
                "propagate_archive": True,
            }
        )
        Relation.create(
            {
                "type_id": rel_type.id,
                "left_partner_id": person.id,
                "right_partner_id": self.rel1.id,
            }
        )

        # Ensure states
        for p in (person, self.rel1):
            p.write({"active": True, "propagated_from_id": False})
        # Enable non-UI propagation so _archive_propagate is called
        icp = self.env["ir.config_parameter"].sudo()
        icp.set_param("partner_archive_propagate.force_outside_ui", "1")
        # Archive the non-company partner
        person.write({"active": False})
        # Person should be inactive
        self.assertFalse(person.active)
        # rel1 should not be touched by relation propagation here
        self.rel1.invalidate_recordset()
        self.assertTrue(self.rel1.active)
        self.assertFalse(
            bool(self.rel1.propagated_from_id),
            "rel1 should not be archived via non-company relation propagation",
        )
        # Reset setting
        icp.set_param("partner_archive_propagate.force_outside_ui", "0")

    def test_show_wizard_button_for_company(self):
        Partners = self.env["res.partner"]
        # org has no children (but relations)
        self.assertFalse(bool(self.org.child_ids))
        # related partners are contacts
        self.rel1.write({"type": "contact"})
        self.rel2.write({"type": "contact"})
        # Force recompute by browsing fresh record
        org = Partners.browse(self.org.id)
        org.invalidate_recordset()
        self.assertTrue(
            org.show_prop_wizard_button,
        )

    def test_action_company_wizard_for_relations(self):
        """If org has no hierarchical contact children but has propagating relation contacts,
        wizard must be opened.
        """
        # org has no hierarchical contact children
        self.assertFalse(bool(self.org.child_ids))
        for p in (self.org, self.rel1, self.rel2):
            p.write({"active": True, "propagated_from_id": False})
        # related partners are contacts
        self.rel1.write({"type": "contact"})
        self.rel2.write({"type": "contact"})
        action = self.org.action_archive_with_contacts()
        self.assertIsInstance(action, dict)
        # it is a wizard
        self.assertEqual(
            action.get("res_model"), "res.partner.archive.propagate.wizard"
        )
        self.assertEqual(action.get("target"), "new")
        wiz = self.env["res.partner.archive.propagate.wizard"].browse(action["res_id"])
        line_partners = wiz.line_ids.mapped("partner_id")
        self.assertIn(self.rel1, line_partners)
        self.assertIn(self.rel2, line_partners)

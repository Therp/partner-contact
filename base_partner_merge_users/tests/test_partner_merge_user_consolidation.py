# Copyright 2025 Therp BV <https://therp.nl>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase


class TestMergePartnerUsers(TransactionCase):
    @classmethod
    def setUpClass(cls):
        # sudo the multiverse here, just in case
        super().setUpClass()
        cls.Partner = cls.env["res.partner"].sudo()
        cls.User = cls.env["res.users"].sudo()
        cls.Groups = cls.env["res.groups"].sudo()
        cls.Log = cls.env["res.users.log"].sudo()
        cls.Wizard = cls.env["base.partner.merge.automatic.wizard"].sudo()
        cls.grp_partner_manager = cls.env.ref("base.group_partner_manager")
        cls.grp_no_one = cls.env.ref("base.group_no_one")
        # person can merge
        cls.env.user.sudo().write({"groups_id": [(4, cls.grp_partner_manager.id)]})
        cls.p1 = cls.Partner.create({"name": "Data", "is_company": False})
        cls.p2 = cls.Partner.create({"name": "Lore.", "is_company": False})
        # create users with different groups, for merging
        cls.u1 = cls.User.create(
            {
                "name": "User Data",
                "login": "data@deepspace.nine",
                "partner_id": cls.p1.id,
                "groups_id": [(4, cls.grp_partner_manager.id)],
            }
        )
        cls.u2 = cls.User.create(
            {
                "name": "User Lore",
                "login": "lore@deepspace.nine",
                "partner_id": cls.p2.id,
                "groups_id": [(4, cls.grp_no_one.id)],
            }
        )

        # Mimic login
        older_log = cls.Log.with_user(cls.u1).create({})
        older = fields.Datetime.now() - timedelta(days=10)
        # needed to actually invoke raw sql for this
        cls.env.cr.execute(
            "UPDATE res_users_log SET create_date = %s WHERE id = %s",
            (fields.Datetime.to_string(older), older_log.id),
        )
        # Data will be merged into Lore
        cls.Log.with_user(cls.u2).create({})

    def test_merge_user(self):
        """Merge partner AND user, unlink partner, archive user"""
        wiz = self.Wizard.create({})
        wiz._merge([self.p1.id, self.p2.id], dst_partner=self.p1)
        # source partner removed
        self.assertFalse(self.p2.exists())
        # fresh read
        self.env.invalidate_all()
        self.assertEqual(self.u2.partner_id.id, self.p1.id)
        self.assertTrue(self.u2.active)
        self.assertFalse(self.u1.active)
        # defuse everything for obsolete user
        self.assertTrue(self.u1.login.startswith("__merged_user_"))
        kept_groups = set(self.u2.groups_id.ids)
        self.assertIn(self.grp_partner_manager.id, kept_groups)
        self.assertIn(self.grp_no_one.id, kept_groups)

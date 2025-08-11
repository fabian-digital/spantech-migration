# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo.exceptions import UserError
from odoo.tests import SavepointCase


class TestProductSequence(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pso = cls.env["product.sequence"]
        cls.iso = cls.env["ir.sequence"]

        cls.ps_01 = cls.pso.create(dict(code="01-001", name="product_code 01-001"))
        cls.ps_02 = cls.pso.create(dict(code="01-002", name="product_code 01-002"))

    def test_product_sequence_equal_ir_sequence(self):
        self.assertTrue(self.ps_01.sequence_id, "Ir Sequence Must Be linked")
        self.assertEqual(
            self.ps_01.code, self.ps_01.sequence_id.code, "Code must be equals"
        )
        self.assertEqual(
            self.ps_01.name, self.ps_01.sequence_id.name, "Name must be equals"
        )

    def test_limit_exceeded_raise(self):
        self.ps_exceeded = self.pso.create(
            dict(code="01-003", name="product_code 01-003")
        )
        self.ps_exceeded.sequence_id.number_next_actual = 1000
        with self.assertRaises(UserError):
            self.ps_exceeded.next_by_id()

    def test_sync_product_sequence_and_ir_sequence(self):
        self.assertEqual(
            self.ps_01.code, self.ps_01.sequence_id.code, "Code must be equals"
        )
        self.assertEqual(
            self.ps_01.name, self.ps_01.sequence_id.name, "Name must be equals"
        )
        self.ps_01.code = "TOTO01-001"
        self.assertEqual(
            self.ps_01.code, self.ps_01.sequence_id.code, "Code must be equals"
        )
        self.ps_01.name = "TOTO Product Code 01-001"
        self.assertEqual(
            self.ps_01.name, self.ps_01.sequence_id.name, "Name must be equals"
        )

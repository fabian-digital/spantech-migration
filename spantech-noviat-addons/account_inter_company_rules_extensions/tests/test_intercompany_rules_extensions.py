# Copyright 2009-2023 Noviat.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import odoo.tests
from odoo import Command
from odoo.exceptions import UserError

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@odoo.tests.tagged("post_install", "-at_install")
class TestInterCompanyInvoiceExtensions(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls, chart_template_ref=None):
        if not chart_template_ref:
            odoo.tests.TransactionCase.setUpClass()
            chart_template = cls.env["account.chart.template"].search([])
            if chart_template:
                chart_template_refs = chart_template[0].get_external_id()
                chart_template_ref = list(chart_template_refs.values())[0]
        if not chart_template_ref:
            cls.tearDownClass()
            # skipTest raises exception
            cls.skipTest(
                cls,
                "Accounting Tests skipped because the user's company "
                "has no chart of accounts.",
            )

        super().setUpClass(chart_template_ref=chart_template_ref)

        cls.company_1 = cls.company_data["company"]
        cls.company_1.rule_type = "invoice_and_refund"
        cls.journal_sale_c1 = cls.company_data["default_journal_sale"]
        cls.journal_sale_refund_c1 = cls.journal_sale_c1.copy(
            default={"alias_name": "customer-refunds"}
        )
        cls.journal_sale_refund_c1.write(
            {
                "name": "Customer Refunds",
                "code": "S-REF",
            }
        )
        cls.journal_sale_interco_c1 = cls.journal_sale_c1.copy(
            default={"alias_name": "intercompany-customer-invoices "}
        )
        cls.journal_sale_interco_c1.write(
            {
                "name": "Intercompany Customer Invoices",
                "code": "S-ICO",
            }
        )

        cls.company_2 = cls.company_data_2["company"]
        cls.company_2.rule_type = "invoice_and_refund"
        cls.journal_purchase_c2 = cls.company_data_2["default_journal_purchase"]
        cls.journal_purchase_interco_c2 = cls.journal_purchase_c2.copy(
            default={"alias_name": "intercompany-vendor-bills"}
        )
        cls.journal_purchase_interco_c2.write(
            {
                "name": "Intercompany Vendor Bills",
                "code": "P-ICO",
            }
        )
        cls.journal_purchase_refund_c2 = cls.journal_purchase_c2.copy(
            default={"alias_name": "intercompany-vendor-refunds"}
        )
        cls.journal_purchase_refund_c2.write(
            {
                "name": "Intercompany Vendor Refunds",
                "code": "P-REF",
            }
        )

        # Create bookkeeper of company 1
        cls.user_c1 = cls.env["res.users"].create(
            {
                "name": "Bookkeeper C1",
                "login": "user1",
                "email": "user1@yourcompany.com",
                "company_id": cls.company_1.id,
                "company_ids": [Command.set(cls.company_1.ids)],
                "groups_id": [
                    Command.set(cls.env.ref("account.group_account_user").ids)
                ],
            }
        )
        # Create customer invoices for company 1
        cls.customer_invoice_c1 = (
            cls.env["account.move"]
            .with_user(cls.user_c1)
            .create(
                {
                    "move_type": "out_invoice",
                    "partner_id": cls.company_2.partner_id.id,
                    "currency_id": cls.env.ref("base.EUR").id,
                    "invoice_line_ids": [
                        (
                            0,
                            0,
                            {
                                "product_id": cls.product_a.id,
                                "price_unit": 1000.0,
                                "quantity": 1.0,
                                "name": "product_a",
                            },
                        )
                    ],
                }
            )
        )
        cls.customer_invoice_interco_c1 = cls.customer_invoice_c1.copy(
            default={"journal_id": cls.journal_sale_interco_c1.id}
        )
        cls.customer_refund_c1 = cls.customer_invoice_c1._reverse_moves(
            default_values_list=[{"journal_id": cls.journal_sale_refund_c1.id}]
        )

        # Create the mappings
        cls.mappings = cls.env[
            "account.reinvoice.journal.mapping.multi.company"
        ].create(
            [
                {
                    "sequence": 10,
                    "journal_out_ids": [
                        Command.set(
                            (cls.journal_sale_c1 + cls.journal_sale_refund_c1).ids
                        )
                    ],
                    "target_company": str(cls.company_2.id),
                    "target_journal_id": cls.journal_purchase_c2.id,
                    "target_refund_journal_id": cls.journal_purchase_refund_c2.id,
                    "company_id": cls.company_1.id,
                },
                {
                    "sequence": 20,
                    "journal_out_ids": [Command.set(cls.journal_sale_interco_c1.ids)],
                    "target_company": str(cls.company_2.id),
                    "target_journal_id": cls.journal_purchase_interco_c2.id,
                    "target_refund_journal_id": cls.journal_purchase_interco_c2.id,
                    "company_id": cls.company_1.id,
                },
            ]
        )

        # Validate invoices
        cls.customer_invoice_c1.action_post()
        cls.customer_invoice_interco_c1.action_post()
        cls.customer_refund_c1.action_post()

    def test_button_draft(self):
        with self.assertRaises(UserError), self.cr.savepoint():
            self.customer_invoice_c1.button_draft()

    def test_button_cancel(self):
        with self.assertRaises(UserError), self.cr.savepoint():
            self.customer_invoice_c1.button_cancel()

    def test_inter_company_prepare_invoice_data(self):
        """
        We test one normal invoice, one normal refund and one intercompany invoice
        """
        supplier_invoice = self.customer_invoice_c1.sudo().intercompany_invoice_id
        supplier_invoice_refund = self.customer_refund_c1.sudo().intercompany_invoice_id
        supplier_invoice_interco = (
            self.customer_invoice_interco_c1.sudo().intercompany_invoice_id
        )

        self.assertEqual(
            supplier_invoice.journal_id.id,
            self.journal_purchase_c2.id,
            "Journal mismatch for normal invoice",
        )
        self.assertEqual(
            supplier_invoice_refund.journal_id.id,
            self.journal_purchase_refund_c2.id,
            "Journal mismatch for normal refund",
        )
        self.assertEqual(
            supplier_invoice_interco.journal_id.id,
            self.journal_purchase_interco_c2.id,
            "Journal mismatch for intercompany invoice",
        )

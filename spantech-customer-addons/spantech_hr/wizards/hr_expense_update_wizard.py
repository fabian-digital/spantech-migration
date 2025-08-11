# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrExpenseLineUpdateWizard(models.TransientModel):
    _name = "hr.expense.update.wizard"
    _description = "Update expense line"
    _inherit = "analytic.mixin"

    company_id = fields.Many2one(comodel_name="res.company", string="Company")
    exp_line_id = fields.Many2one(comodel_name="hr.expense", string="HR Expense")
    account_id = fields.Many2one(
        comodel_name="account.account",
        domain="[('company_id', '=', company_id), ('deprecated', '=', False), "
        "('account_type', 'not in', "
        "('asset_receivable','liability_payable','asset_cash','liability_credit_card'))]",
    )
    product_id = fields.Many2one(
        comodel_name="product.product",
        domain=[("can_be_expensed", "=", True)],
        string="Category",
        required=True,
    )
    tax_ids = fields.Many2many(
        comodel_name="account.tax",
        string="Taxes",
        compute="_compute_tax_ids",
        store=True,
        readonly=False,
        precompute=True,
        context={"active_test": False},
        check_company=True,
    )

    @api.onchange("product_id")
    def _onchange_product_id(self):
        account = self.product_id.product_tmpl_id._get_product_accounts()["expense"]
        if account:
            self.account_id = account
        self.tax_ids = self.product_id.supplier_taxes_id.filtered(
            lambda r: r.company_id == self.company_id
        )

    def update(self):
        self.exp_line_id.product_id = self.product_id
        self.exp_line_id.tax_ids = self.tax_ids
        self.exp_line_id.account_id = self.account_id
        self.exp_line_id.analytic_distribution = self.analytic_distribution

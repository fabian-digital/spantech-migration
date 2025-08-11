# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    expense_mandatory_attachment = fields.Boolean(
        string="Expense - Mandatory receipt", default=False
    )
    is_expense_cashwithdrawal = fields.Boolean(
        string="Expense - Cash Withdrawal", default=False
    )

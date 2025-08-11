# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    expense_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Expense Journal",
        domain=[("is_spantech_expense", "=", True)],
        help="Default journal used for expenses paid "
        "by employee and need to be reimbursed",
    )
    expense_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Expense Payment Mode",
        help="Default payment mode used for expenses paid "
        "by employee and need to be reimbursed",
    )

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    expense_journal_id = fields.Many2one(
        comodel_name="account.journal",
        related="company_id.expense_journal_id",
        readonly=False,
    )
    expense_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        related="company_id.expense_payment_mode_id",
        readonly=False,
    )

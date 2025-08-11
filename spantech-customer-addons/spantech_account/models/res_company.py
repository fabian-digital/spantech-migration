# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class Company(models.Model):
    _inherit = "res.company"

    prepayment_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Prepayment Journal",
        domain=[("type", "=", "purchase")],
    )
    prepayment_payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode", string="Prepayment Payment Mode"
    )

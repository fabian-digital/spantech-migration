# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    ico_conso_pl_move_id = fields.Many2one(
        comodel_name="account.move",
        string="ICO P&L Consolidation entry",
        ondelete="set null",
    )
    ico_conso_bs_move_id = fields.Many2one(
        comodel_name="account.move",
        string="ICO BS Consolidation entry",
        ondelete="set null",
    )

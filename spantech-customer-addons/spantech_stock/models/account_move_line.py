# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    line_origin = fields.Char(
        string="Source Document", compute="_compute_line_origin", store=True
    )

    @api.depends(
        "stock_move_id.origin", "move_id.invoice_origin", "mrp_production_id.origin"
    )
    def _compute_line_origin(self):
        for move_line in self:
            if move_line.mrp_production_id and move_line.mrp_production_id.origin:
                move_line.line_origin = move_line.mrp_production_id.origin
            elif move_line.stock_move_id and move_line.stock_move_id.origin:
                move_line.line_origin = move_line.stock_move_id.origin
            elif move_line.move_id.invoice_origin:
                move_line.line_origin = move_line.move_id.invoice_origin
            else:
                move_line.line_origin = False

# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    date = fields.Datetime(
        compute="_compute_date", string="Move/Valuation Date", store=True
    )

    @api.depends("stock_move_id.date", "create_date")
    def _compute_date(self):
        for valuation in self:
            if valuation.stock_move_id:
                valuation.date = valuation.stock_move_id.date
            else:
                valuation.date = valuation.create_date

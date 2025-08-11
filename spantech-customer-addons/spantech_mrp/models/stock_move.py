# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def action_product_forecast_report(self):
        action = super().action_product_forecast_report()
        if self.raw_material_production_id.analytic_account_id:
            action["context"][
                "mrp_analytic_account"
            ] = self.raw_material_production_id.analytic_account_id.id
        return action

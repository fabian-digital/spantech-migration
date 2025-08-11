# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _get_stock_move_values(
        self,
        product_id,
        product_qty,
        product_uom,
        location_id,
        name,
        origin,
        company_id,
        values,
    ):
        move_values = super()._get_stock_move_values(
            product_id,
            product_qty,
            product_uom,
            location_id,
            name,
            origin,
            company_id,
            values,
        )
        if "analytic_distribution" in values and values["analytic_distribution"]:
            move_values["analytic_distribution"] = values["analytic_distribution"]
        elif "analytic_account_id" in values and values["analytic_account_id"]:
            analytic_account_id = values["analytic_account_id"]
            if not isinstance(analytic_account_id, int):
                analytic_account_id = analytic_account_id.id
            move_values["analytic_distribution"] = {analytic_account_id: 100}
        return move_values

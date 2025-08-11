# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockRule(models.Model):
    _inherit = "stock.rule"

    def _prepare_purchase_order(self, company_id, origins, values):
        vals = super()._prepare_purchase_order(company_id, origins, values)
        values = values[0]
        if values.get("group_id", False):
            group_id = values.get("group_id")
            if group_id.sale_id:
                if group_id.sale_id.analytic_account_id:
                    vals["analytic_distribution"] = {
                        group_id.sale_id.analytic_account_id.id: 100
                    }
                if group_id.sale_id.user_id:
                    vals["user_id"] = group_id.sale_id.user_id.id
        return vals

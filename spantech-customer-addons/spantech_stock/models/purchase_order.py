# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _prepare_purchase_order_line(
        self, product_id, product_qty, product_uom, company_id, supplier, po
    ):
        res = super()._prepare_purchase_order_line(
            product_id, product_qty, product_uom, company_id, supplier, po
        )
        if self.env.context.get("sale_line_id", False):
            order_line = self.env["sale.order.line"].browse(
                self.env.context.get("sale_line_id", False)
            )
            res["sale_line_id"] = order_line.id
            if order_line.order_id.analytic_account_id:
                res["analytic_distribution"] = {
                    order_line.order_id.analytic_account_id.id: 100
                }
        return res

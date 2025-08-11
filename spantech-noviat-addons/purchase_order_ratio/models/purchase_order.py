# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    qty_received_ratio_total = fields.Float(
        string="Received ratio",
        compute="_compute_qty_received_ratio_total",
        store=True,
    )

    qty_invoiced_ratio_total = fields.Float(
        string="Invoiced ratio",
        compute="_compute_qty_invoiced_ratio_total",
        store=True,
    )

    @api.depends(
        "order_line",
        "order_line.qty_received",
        "order_line.qty_received_method",
        "order_line.product_uom_qty",
    )
    def _compute_qty_received_ratio_total(self):
        for purchase in self:
            total_ordered_qty = 0.0
            total_received_qty = 0.0
            for line in purchase.order_line:
                if line.qty_received_method == "stock_moves":
                    total_ordered_qty += line.product_uom_qty
                    total_received_qty += line.qty_received

            if total_ordered_qty == 0.0 and total_received_qty > 0.0:
                purchase.qty_received_ratio_total = 100
            elif total_ordered_qty != 0.0:
                purchase.qty_received_ratio_total = (
                    total_received_qty / total_ordered_qty
                ) * 100.0
            else:
                purchase.qty_received_ratio_total = 0.0

    @api.depends(
        "invoice_status",
        "order_line",
        "order_line.qty_invoiced",
    )
    def _compute_qty_invoiced_ratio_total(self):
        for purchase in self:
            total_ordered_qty = 0.0
            total_invoiced_qty = 0.0
            for line in purchase.order_line:
                total_ordered_qty += line.product_uom_qty
                total_invoiced_qty += line.qty_invoiced
            if total_ordered_qty == 0.0 and total_invoiced_qty > 0.0:
                purchase.qty_invoiced_ratio_total = 100
            elif total_ordered_qty != 0.0:
                purchase.qty_invoiced_ratio_total = (
                    total_invoiced_qty / total_ordered_qty
                ) * 100.0
            else:
                purchase.qty_invoiced_ratio_total = 0.0

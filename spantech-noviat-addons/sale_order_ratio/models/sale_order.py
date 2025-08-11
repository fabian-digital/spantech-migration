# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    qty_delivered_ratio_total = fields.Float(
        string="Delivered ratio",
        compute="_compute_qty_delivered_ratio_total",
        store=True,
    )

    qty_invoiced_ratio_total = fields.Float(
        string="Invoiced ratio",
        compute="_compute_qty_invoiced_ratio_total",
        store=True,
    )

    @api.depends(
        "order_line",
        "order_line.qty_delivered",
        "order_line.qty_delivered_method",
        "order_line.product_uom_qty",
    )
    def _compute_qty_delivered_ratio_total(self):
        for sale in self:
            total_ordered_qty = 0.0
            total_delivered_qty = 0.0
            for line in sale.order_line:
                if line.qty_delivered_method == "stock_move":
                    total_ordered_qty += line.product_uom_qty
                    total_delivered_qty += line.qty_delivered

            if total_ordered_qty == 0.0 and total_delivered_qty > 0.0:
                sale.qty_delivered_ratio_total = 100
            elif total_ordered_qty != 0.0:
                sale.qty_delivered_ratio_total = (
                    total_delivered_qty / total_ordered_qty
                ) * 100.0
            else:
                sale.qty_delivered_ratio_total = 0.0

    @api.depends(
        "order_line",
        "order_line.qty_invoiced",
        "order_line.invoice_status",
    )
    def _compute_qty_invoiced_ratio_total(self):
        for sale in self:
            total_ordered_qty = 0.0
            total_invoiced_qty = 0.0
            for line in sale.order_line.filtered(lambda ol: not ol.display_type):
                total_ordered_qty += line.product_uom_qty
                total_invoiced_qty += line.qty_invoiced
            if total_ordered_qty == 0.0 and total_invoiced_qty > 0.0:
                sale.qty_invoiced_ratio_total = 100
            elif total_ordered_qty != 0.0:
                sale.qty_invoiced_ratio_total = (
                    total_invoiced_qty / total_ordered_qty
                ) * 100.0
            else:
                sale.qty_invoiced_ratio_total = 0.0

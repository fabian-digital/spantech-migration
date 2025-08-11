# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    # Not the OCA amount_uninvoiced because it take the "control policy" into account
    amount_total_uninvoiced = fields.Monetary(
        string="Uninvoiced Amount",
        readonly=True,
        compute="_compute_amount_total_uninvoiced",
        tracking=True,
        store=True,
    )

    @api.depends("order_line.price_uninvoiced")
    def _compute_amount_total_uninvoiced(self):
        for order in self:
            order.amount_total_uninvoiced = sum(
                order.order_line.mapped("price_uninvoiced")
            )


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.depends(
        "product_qty",
        "qty_invoiced",
        "qty_received",
        "product_id",
        "product_uom",
        "price_unit",
    )
    def _compute_price_uninvoiced(self):
        for order_line in self:
            qty = order_line.product_qty - order_line.qty_invoiced
            # Logic from OCA module purchase_order_uninvoiced_amount
            price_unit = (
                order_line.price_subtotal / order_line.product_qty
                if order_line.product_qty
                else order_line.price_unit
            )
            order_line.price_uninvoiced = order_line.currency_id.round(qty * price_unit)

    price_uninvoiced = fields.Monetary(
        string="Uninvoiced Amount",
        compute="_compute_price_uninvoiced",
        store=True,
    )
    order_type = fields.Many2one(
        related="order_id.order_type",
        store=True,
    )

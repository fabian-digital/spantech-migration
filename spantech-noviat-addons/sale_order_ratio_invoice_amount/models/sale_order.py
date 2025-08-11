# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    amount_invoiced_ratio_total = fields.Float(
        string="Invoiced Ratio",
        compute="_compute_amount_invoiced_ratio_total",
        store=True,
    )

    @api.depends(
        "invoiced_amount",
        "amount_total",
    )
    def _compute_amount_invoiced_ratio_total(self):
        for sale in self:
            amount_invoiced_ratio_total = 0
            if sale.amount_total != 0.0:
                amount_invoiced_ratio_total = (sale.invoiced_amount / sale.amount_total) * 100
            sale.amount_invoiced_ratio_total = amount_invoiced_ratio_total

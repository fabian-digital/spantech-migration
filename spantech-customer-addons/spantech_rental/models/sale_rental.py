# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleRental(models.Model):
    _inherit = "sale.rental"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        related="start_order_id.analytic_account_id",
        store=True,
    )
    stock_move_ids = fields.One2many(
        comodel_name="stock.move",
        inverse_name="rental_id",
    )

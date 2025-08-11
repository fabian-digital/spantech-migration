# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models
from odoo.tools import float_is_zero

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    weight_done = fields.Float(
        compute="_compute_weight_done",
        digits="Stock Weight",
        store=True,
        compute_sudo=True,
    )

    @api.depends("product_id", "product_uom_qty", "product_uom", "quantity_done")
    def _compute_weight_done(self):
        moves_with_weight = self.filtered(lambda moves: moves.product_id.weight > 0.00)
        for move in moves_with_weight:
            move.weight_done = move.quantity_done * move.product_id.weight
        (self - moves_with_weight).weight_done = 0

    def action_set_to_zero(self):
        for rec in self:
            if rec.state not in ["done", "cancel"]:
                rec.quantity_done = 0

    def _create_out_svl(self, forced_quantity=None):
        svls = super()._create_out_svl(forced_quantity)
        for svl in svls:
            slvsm = svl.stock_move_id
            if (
                slvsm.origin_returned_move_id
                and slvsm.origin_returned_move_id.sudo().stock_valuation_layer_ids
            ):
                layers = slvsm.origin_returned_move_id.sudo().stock_valuation_layer_ids
                layers |= layers.stock_valuation_layer_ids
                quantity = sum(layers.mapped("quantity"))
                value = sum(layers.mapped("value"))
                unit_cost = (
                    layers.currency_id.round(value / quantity)
                    if not float_is_zero(
                        quantity, precision_rounding=layers.uom_id.rounding
                    )
                    else 0
                )
                if slvsm.quantity_done == svl.quantity:
                    svl.value = value
                else:
                    svl.value = (
                        (value / quantity) * svl.quantity
                        if not float_is_zero(
                            quantity, precision_rounding=layers.uom_id.rounding
                        )
                        else 0
                    )
                svl.unit_cost = unit_cost
        return svls


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _get_aggregated_product_quantities(self, **kwargs):
        res = super()._get_aggregated_product_quantities()
        sorted_res = dict(sorted(res.items(), reverse=True))
        return dict(sorted_res)

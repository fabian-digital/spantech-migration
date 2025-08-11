# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    rental = fields.Boolean(related="sale_line_id.rental", store=True)
    rental_id = fields.Many2one(
        comodel_name="sale.rental", related="sale_line_id.rental_id", store=True
    )
    rented_product_id = fields.Many2one(
        comodel_name="product.product",
        related="rental_id.rented_product_id",
        store=True,
    )
    rental_qty = fields.Float(related="rental_id.rental_qty", store=True)
    start_order_id = fields.Many2one(
        comodel_name="sale.order", related="rental_id.start_order_id", store=True
    )
    rental_state = fields.Selection(related="rental_id.state", store=True)

    def _action_cancel(self):
        rental_in_move = self.filtered(lambda m: m.rental).move_dest_ids
        res = super()._action_cancel()
        if rental_in_move:
            rental_in_move._action_cancel()
            pickings = rental_in_move.mapped("picking_id").filtered(
                lambda p: p.state == "cancel"
            )
            pickings.write({"state": "waiting"})
        return res

    def _action_confirm(self, merge=True, merge_into=False):
        moves = super()._action_confirm(merge, merge_into)
        for move in moves:
            if move.rental and all(move.move_orig_ids.mapped("rental")):
                move.picking_id.move_ids.filtered(
                    lambda m: m.state == "cancel"
                ).unlink()
        return moves

# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    rental_picking = fields.Boolean(compute="_compute_rental_picking", store=True)

    @api.depends("move_ids.rental_id")
    def _compute_rental_picking(self):
        for picking in self:
            if any(move.rental for move in picking.move_ids):
                picking.rental_picking = True
            else:
                picking.rental_picking = False

    def action_open_stock_move_link_rental(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "spantech_rental.stock_move_link_rental_wizard_action"
        )
        action.update({"context": {"default_picking_id": self.id}})
        return action

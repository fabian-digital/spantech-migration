# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import json

from odoo import api, fields, models


class StockMoveLinkRentalWizard(models.TransientModel):
    _name = "stock.move.link.rental.wizard"

    picking_id = fields.Many2one(comodel_name="stock.picking", required=True)
    line_ids = fields.One2many(
        comodel_name="stock.move.link.rental.line.wizard", inverse_name="wizard_id"
    )

    @api.onchange("picking_id")
    def _onchange_picking_id(self):
        self.ensure_one()
        moves_without_sale_line = self.picking_id.move_ids_without_package.filtered(
            lambda m: not m.sale_line_id
        )
        if moves_without_sale_line:
            sale_line_ids = self.picking_id.move_ids.mapped("sale_line_id")
            for move in moves_without_sale_line:
                vals = {"wizard_id": self.id, "stock_move_id": move.id}
                if len(sale_line_ids) == 1:
                    vals["sale_line_id"] = sale_line_ids[0].id
                self.line_ids.create(vals)

    def action_link(self):
        self.ensure_one()
        for line in self.line_ids:
            if line.stock_move_id and line.sale_line_id:
                line.stock_move_id.write({"sale_line_id": line.sale_line_id.id})


class StockMoveLinkRentalLineWizard(models.TransientModel):
    _name = "stock.move.link.rental.line.wizard"

    wizard_id = fields.Many2one(comodel_name="stock.move.link.rental.wizard")
    stock_move_id = fields.Many2one(comodel_name="stock.move")
    product_id = fields.Many2one(
        comodel_name="product.product", related="stock_move_id.product_id"
    )
    sale_line_id = fields.Many2one(comodel_name="sale.order.line", string="Rental Line")
    sale_line_id_domain = fields.Char(
        compute="_compute_sale_line_id_domain", store=True
    )

    @api.depends("wizard_id.picking_id")
    def _compute_sale_line_id_domain(self):
        for line in self:
            sale_line_ids = line.wizard_id.picking_id.move_ids.mapped(
                "sale_line_id"
            ).ids
            if sale_line_ids:
                line.sale_line_id_domain = json.dumps([("id", "in", sale_line_ids)])
            else:
                line.sale_line_id_domain = json.dumps([])

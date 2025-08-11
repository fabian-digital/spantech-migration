# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class MrpBom(models.Model):
    _inherit = "mrp.bom"

    component_stock_move_ids = fields.Many2many(
        comodel_name="stock.move", compute="_compute_component_stock_move_ids"
    )
    component_stock_move_count = fields.Integer(
        compute="_compute_component_stock_move_ids"
    )

    @api.model
    def default_get(self, fields_list):
        self = self.with_context(**dict(self.env.context, default_company_id=None))
        return super().default_get(fields_list)

    def _compute_component_stock_move_ids(self):
        for bom in self:
            if bom.bom_line_ids:
                moves = bom.bom_line_ids.mapped("product_id").mapped("stock_move_ids")
                bom.component_stock_move_ids = moves
                bom.component_stock_move_count = len(moves)
            else:
                bom.component_stock_move_ids = False
                bom.component_stock_move_count = 0

    def action_component_stock_moves(self):
        self.ensure_one()
        action_data = self.env["ir.actions.act_window"]._for_xml_id(
            "stock.stock_move_action"
        )
        action_data["domain"] = [("id", "in", self.component_stock_move_ids.ids)]
        return action_data

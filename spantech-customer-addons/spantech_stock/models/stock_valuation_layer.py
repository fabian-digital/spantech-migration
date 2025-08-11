# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class StockValuationLayer(models.Model):
    _inherit = "stock.valuation.layer"

    operation_type = fields.Selection(
        [
            ("none", "None"),
            ("incoming", "Receipt"),
            ("outgoing", "Delivery"),
            ("internal", "Internal Transfer"),
            ("outgoing_return", "Outgoing Return"),
            ("incoming_return", "Incoming Return"),
            ("return", "Return"),
            ("inventory", "Inventory"),
            ("manufacture", "Manufacturing"),
            ("opening", "Opening"),
            ("valuation", "Manual Valuation"),
        ],
        string="Type of Operation",
        compute="_compute_operation_type",
        store=True,
    )
    is_opening = fields.Boolean()
    force_date = fields.Datetime()

    @api.depends(
        "stock_move_id.picking_code",
        "stock_move_id.location_id",
        "stock_move_id.move_line_ids",
        "stock_move_id",
        "is_opening",
    )
    def _compute_operation_type(self):
        for valuation in self:
            if valuation.is_opening:
                valuation.operation_type = "opening"
            elif valuation.stock_move_id:
                if valuation.stock_move_id.origin_returned_move_id:
                    if valuation.stock_move_id.picking_code == "incoming":
                        valuation.operation_type = "incoming_return"
                    if valuation.stock_move_id.picking_code == "outgoing":
                        valuation.operation_type = "outgoing_return"
                    else:
                        valuation.operation_type = "return"
                elif valuation.stock_move_id.picking_code:
                    valuation.operation_type = valuation.stock_move_id.picking_code
                else:
                    if valuation.stock_move_id.is_inventory:
                        valuation.operation_type = "inventory"
                    elif any(
                        move_line.workorder_id or move_line.production_id
                        for move_line in valuation.stock_move_id.move_line_ids
                    ):
                        valuation.operation_type = "manufacture"
                    elif (
                        valuation.stock_move_id.production_id
                        or valuation.stock_move_id.workorder_id
                    ):
                        valuation.operation_type = "manufacture"
                    else:
                        valuation.operation_type = "inventory"
            else:
                valuation.operation_type = "valuation"

    @api.depends("stock_move_id", "create_date", "force_date")
    def _compute_date(self):
        for valuation in self:
            if (
                valuation.operation_type in ("valuation", "inventory", "opening")
                and valuation.force_date
            ):
                valuation.date = valuation.force_date
            else:
                super(StockValuationLayer, valuation)._compute_date()
        return

    def action_set_is_opening(self):
        for valuation in self:
            valuation.is_opening = not valuation.is_opening

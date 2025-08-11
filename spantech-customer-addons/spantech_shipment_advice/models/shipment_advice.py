# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ShipmentAdvice(models.Model):
    _inherit = "shipment.advice"

    information = fields.Text()

    @api.depends(
        "loaded_move_line_ids.result_package_id.shipping_weight",
        "loaded_move_line_without_package_ids",
        "loaded_move_line_without_package_ids.qty_done",
    )
    def _compute_total_load(self):
        res = super()._compute_total_load()
        for shipment in self:
            if shipment.total_load == 0.0:
                total_weight = 0.0
                for move_line in shipment.loaded_move_line_without_package_ids:
                    uom_qty = move_line.product_uom_id._compute_quantity(
                        move_line.qty_done, move_line.product_uom_id
                    )
                    total_weight += uom_qty * move_line.product_id.weight
                shipment.total_load = total_weight
        return res

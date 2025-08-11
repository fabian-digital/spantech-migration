# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockImmediateTransferLine(models.TransientModel):
    _name = "change.state.warning.wizard"
    _description = "Change state warning wizard"

    purchase_order_id = fields.Many2one(
        string="Purchase order", comodel_name="purchase.order", required=True
    )

    def process(self):
        self.purchase_order_id.with_context(from_wizard=True).button_draft()

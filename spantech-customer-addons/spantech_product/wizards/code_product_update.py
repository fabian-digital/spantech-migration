# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class CodeProductUpdate(models.TransientModel):
    _name = "code.product.update"
    _description = "Wizard to update the Product Codes"

    sequence_id = fields.Many2one(comodel_name="product.sequence")
    number_next_actual = fields.Integer(related="sequence_id.number_next_actual")

    def action_apply_code(self):
        for rec in self:
            sequence = rec.sequence_id.next_by_id()
            self.env[self.env.context.get("active_model")].browse(
                self.env.context.get("active_id")
            ).write({"default_code": sequence, "barcode": sequence})

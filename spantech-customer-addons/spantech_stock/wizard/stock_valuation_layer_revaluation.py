from odoo import _, fields, models
from odoo.exceptions import UserError


class StockValuationLayerRevaluation(models.TransientModel):
    _inherit = "stock.valuation.layer.revaluation"

    force_date = fields.Date()

    def action_validate_revaluation(self):
        start = fields.Datetime.now()
        result = super().action_validate_revaluation()
        if self.force_date and self.property_valuation != "real_time":
            valuation_layer = self.env["stock.valuation.layer"].search(
                [
                    ("company_id", "=", self.company_id.id),
                    ("product_id", "=", self.product_id.id),
                    ("value", "=", self.added_value),
                    ("quantity", "=", 0),
                    ("create_date", ">=", start),
                ],
            )
            # Check if one and only one valuation_layer is found
            if len(valuation_layer) != 1:
                raise UserError(
                    _(
                        "Error to force the date on Product Revaluation.\n"
                        "Re-try in a few seconds."
                    )
                )
            valuation_layer.force_date = self.force_date
        return result

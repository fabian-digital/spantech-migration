from odoo import models


class StockQuantityHistory(models.TransientModel):
    _inherit = "stock.quantity.history"

    def open_at_date(self):
        action = super().open_at_date()
        active_model = self.env.context.get("active_model")
        if active_model == "stock.valuation.layer":
            domain = action["domain"]
            for i, dom in enumerate(domain):
                if isinstance(dom, tuple) and dom[0] == "create_date":
                    domain[i] = ("date", "<=", self.inventory_datetime)
            action["domain"] = domain
        return action

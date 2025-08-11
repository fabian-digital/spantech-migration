# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):
    _inherit = "stock.picking"

    force_date = fields.Date()

    def _action_done(self):
        res = super()._action_done()
        force_date = False
        if self.force_date:
            force_date = self.force_date
        elif self.env.context.get("force_date"):
            force_date = self.env.context.get("force_date")
        if force_date:
            self.write({"date_done": force_date})
        return res
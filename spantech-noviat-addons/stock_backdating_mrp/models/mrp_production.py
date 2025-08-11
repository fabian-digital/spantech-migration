# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    force_date = fields.Date()

    def button_mark_done(self):
        if self.force_date:
            self = self.with_context(force_date=self.force_date)
        res = super().button_mark_done()
        force_date = False
        if self.force_date:
            force_date = self.force_date
        elif self.env.context.get("force_date"):
            force_date = self.env.context.get("force_date")
        if force_date:
            self.write({"date_finished": force_date})
        return res

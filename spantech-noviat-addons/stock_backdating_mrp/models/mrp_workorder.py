# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MrpWorkorder(models.Model):
    _inherit = "mrp.workorder"

    def button_finish(self):
        res = super().button_finish()
        self._set_finished_date_from_force_date()
        return res

    def button_done(self):
        res = super().button_done()
        self._set_finished_date_from_force_date()
        return res

    def _set_finished_date_from_force_date(self):
        for workorder in self:
            force_date = False
            if workorder.production_id and workorder.production_id.force_date:
                force_date = workorder.production_id.force_date
            elif self.env.context.get("force_date"):
                force_date = self.env.context.get("force_date")
            if force_date:
                workorder.with_context(bypass_duration_calculation=True).write(
                    {"date_finished": force_date}
                )

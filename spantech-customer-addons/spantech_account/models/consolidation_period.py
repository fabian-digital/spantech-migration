# Copyright 2009-2025 Noviat.
# License AGPL-3 or later (https://www.gnu.org/licenses/apgl).

from odoo import fields, models


class ConsolidationPeriod(models.Model):
    _inherit = "consolidation.period"

    version = fields.Char()

    def _compute_display_dates(self):
        res = super()._compute_display_dates()
        for rec in self:
            if rec.version:
                rec.display_dates += " " + rec.version
        return res

    def action_copy_period(self):
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "spantech_account.consolidation_period_copy_action"
        )
        action.update(
            {
                "context": {
                    "conso_period_id": self.id,
                    "default_date_analysis_begin": self.date_analysis_begin,
                    "default_date_analysis_end": self.date_analysis_end,
                },
            }
        )
        return action

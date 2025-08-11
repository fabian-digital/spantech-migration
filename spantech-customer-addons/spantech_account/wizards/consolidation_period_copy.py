# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ConsolidationPeriodCopy(models.TransientModel):
    _name = "consolidation.period.copy"
    _description = "Copy Consolidation Period"

    date_analysis_begin = fields.Date(string="Start Date", required=True)
    date_analysis_end = fields.Date(string="End Date", required=True)
    version = fields.Char()

    def copy_period(self):
        period_old = self.env["consolidation.period"].browse(
            self.env.context["conso_period_id"]
        )
        period_new = period_old.copy()
        # copy also conso journals since copy=False for journal_ids
        # we don't need to do this for the journals lines since copy has been set
        # cf. spantech_account/models.consolidation_journal.py
        for j_old in period_old.journal_ids.filtered(lambda r: not r.auto_generated):
            j_old.copy(default={"period_id": period_new.id})
        period_new.date_analysis_begin = self.date_analysis_begin
        period_new.date_analysis_end = self.date_analysis_end
        period_new.version = self.version
        period_new.generate_guessed_company_periods()
        period_new.action_generate_journals()
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "account_consolidation.consolidation_period_action"
        )
        view = self.env.ref("account_consolidation.consolidation_period_form")
        del action["views"]
        action.update(
            {
                "view_mode": "form",
                "view_id": view.id,
                "res_id": period_new.id,
            }
        )
        return action

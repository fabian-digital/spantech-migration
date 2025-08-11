# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = "project.project"

    company_id = fields.Many2one(required=False)
    project_type = fields.Selection(
        related="analytic_account_id.project_type", readonly=False, store=True
    )
    customer_reference = fields.Char(
        related="analytic_account_id.customer_reference", readonly=False, store=True
    )

    @api.model
    def _create_analytic_account_from_values(self, values):
        analytic_account = super()._create_analytic_account_from_values(values)
        analytic_values = {
            "company_id": False,
            "project_type": values.get("project_type"),
            "customer_reference": values.get("customer_reference"),
            "approver_id": values.get("user_id"),
        }
        analytic_account.write(analytic_values)
        values["name"] = analytic_account.name
        return analytic_account

    @api.onchange("analytic_account_id")
    def _onchange_analytic_account_id(self):
        if self.analytic_account_id:
            self.update(
                {
                    "project_type": self.analytic_account_id.project_type,
                    "partner_id": self.analytic_account_id.partner_id.id,
                    "customer_reference": self.analytic_account_id.customer_reference,
                    "user_id": self.analytic_account_id.approver_id.id,
                }
            )

    def action_view_tasks(self):
        action = super().action_view_tasks()
        action["context"].update(
            {
                "search_default_hide_sub_task": True,
            }
        )
        return action

    def action_open_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "res_model": "timesheet.itl.report.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_project_ids": self.ids},
        }

# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = "project.task"

    ticket_ids = fields.One2many(
        string="Tickets", comodel_name="helpdesk.ticket", inverse_name="project_task_id"
    )
    ticket_count = fields.Integer(compute="_compute_ticket_count")

    def _compute_ticket_count(self):
        for project in self:
            project.ticket_count = len(project.ticket_ids)

    def action_open_helpdesk_ticket_view(self):
        return {
            "name": "Tickets",
            "type": "ir.actions.act_window",
            "res_model": "helpdesk.ticket",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.ticket_ids.ids)],
            "context": {
                "default_analytic_account_id": self.analytic_account_id.id,
                "default_project_task_id": self.id,
            },
        }

# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    project_task_id = fields.Many2one(
        string="Task",
        comodel_name="project.task",
        domain="[('analytic_account_id', '=', analytic_account_id)]",
    )

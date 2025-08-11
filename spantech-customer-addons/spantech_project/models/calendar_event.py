# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CalendarEvent(models.Model):
    _inherit = "calendar.event"

    task_id = fields.Many2one(comodel_name="project.task", string="Task")

    def write(self, values):
        if "task_id" in values and values["task_id"]:
            values["name"] = self.env["project.task"].browse(values["task_id"]).name
        return super().write(values)

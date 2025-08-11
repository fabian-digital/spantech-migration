# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class ProjectPerformanceHistory(models.Model):
    _name = "project.performance.history"
    _description = "Project Performance History"

    date = fields.Datetime()
    project_id = fields.Many2one(comodel_name="project.project")
    performance = fields.Float()
    performance_indicator_status = fields.Selection(
        selection=[
            ("no", "No Man-Days"),
            ("good", "Good"),
            ("danger", "Danger"),
            ("bad", "Bad"),
        ],
    )
    man_days_consumption = fields.Float(string="Man-Days Consumption")
    project_completion = fields.Float()
    budgeted_man_days = fields.Float(string="Budgeted Man-Days")
    allocated_man_days = fields.Float(string="Allocated Man-Days")
    actual_man_days = fields.Integer(string="Actual Man-Days (YTD)")
    scheduled_man_days = fields.Integer(
        string="Scheduled Man-Days based on Completion (YTD)"
    )
    man_days_overconsumed = fields.Integer(string="Man-Days Over-Consumed")
    calendar_progression = fields.Float()
    date_start = fields.Datetime(string="Start Date")
    date_deadline = fields.Datetime(string="Deadline")
    calendar_day_left = fields.Integer()

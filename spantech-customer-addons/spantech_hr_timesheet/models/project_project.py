# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class ProjectProject(models.Model):
    _inherit = "project.project"

    hours_in_man_days = fields.Float(default=8.0)
    budgeted_man_days = fields.Float()
    task_completion_danger_threshold_min = fields.Integer(default=-10)
    task_completion_danger_threshold_max = fields.Integer(default=-1)

    calendar_day_left = fields.Integer(compute="_compute_day_left")
    allocated_man_days = fields.Float(compute="_compute_man_days", store=True)
    actual_man_days = fields.Integer(compute="_compute_man_days", store=True)
    scheduled_man_days = fields.Integer(compute="_compute_man_days", store=True)
    man_days_overconsumed = fields.Integer(compute="_compute_man_days", store=True)

    man_days_consumption = fields.Float(compute="_compute_man_days", store=True)
    calendar_progression = fields.Float(compute="_compute_day_left")
    project_completion = fields.Float(compute="_compute_man_days", store=True)
    performance = fields.Float(compute="_compute_man_days", store=True)
    performance_indicator_status = fields.Char(compute="_compute_man_days", store=True)

    project_performance_ids = fields.One2many(
        comodel_name="project.performance.history", inverse_name="project_id"
    )

    @api.depends("date", "date_start")
    def _compute_day_left(self):
        for project in self:
            calendar_day_left = 0
            calendar_progression = 0
            today = fields.Date.today()
            if project.date:
                calendar_day_left = (project.date - today).days
                if project.date_start and project.date_start <= today:
                    project_duration = (project.date - project.date_start).days + 1
                    project_started_days = ((today - project.date_start).days) + 1
                    calendar_progression = min(
                        100, abs(project_started_days / project_duration) * 100
                    )
            project.calendar_day_left = max(calendar_day_left, 0)
            project.calendar_progression = calendar_progression

    @api.depends(
        "hours_in_man_days",
        "budgeted_man_days",
        "task_ids.allocated_man_days",
        "task_ids.timesheet_ids",
        "performance",
        "task_completion_danger_threshold_min",
        "task_completion_danger_threshold_max",
        "task_ids.timesheet_type",
    )
    def _compute_man_days(self):
        for project in self:
            allocated_man_days = actual_man_days = scheduled_man_days = performance = 0
            for task in project.task_ids.filtered(
                lambda t: t.timesheet_type == "installation"
            ):
                allocated_man_days += task.allocated_man_days
                scheduled_man_days += (
                    task.task_completion / 100 * task.allocated_man_days
                )
                for time in task.timesheet_ids:
                    actual_man_days += time.unit_amount
            if project.hours_in_man_days != 0:
                project.actual_man_days = round(
                    (actual_man_days / project.hours_in_man_days), 0
                )
            if project.budgeted_man_days != 0:
                project.man_days_consumption = (
                    project.actual_man_days / project.budgeted_man_days
                ) * 100
            project.scheduled_man_days = round(scheduled_man_days, 0)
            project.allocated_man_days = allocated_man_days
            if project.allocated_man_days != 0:
                project.project_completion = (
                    project.scheduled_man_days / project.allocated_man_days
                ) * 100
                performance = project.project_completion - (
                    (project.actual_man_days / project.allocated_man_days) * 100
                )
            project.performance = performance
            project.get_performance_indicator()
            project.man_days_overconsumed = (
                project.actual_man_days - project.scheduled_man_days
            )

    def get_performance_indicator(self):
        if not self.performance:
            self.performance_indicator_status = "no"
        elif self.performance < self.task_completion_danger_threshold_min:
            self.performance_indicator_status = "bad"
        elif self.performance <= self.task_completion_danger_threshold_max:
            self.performance_indicator_status = "danger"
        elif self.performance > self.task_completion_danger_threshold_max:
            self.performance_indicator_status = "good"
        else:
            self.performance_indicator_status = "no"

    def get_panel_data(self):
        panel_data = super().get_panel_data()
        panel_data["performance_items"] = self.get_performance_items()
        return panel_data

    def get_performance_items(self):
        return {
            "allocated_man_days": self.allocated_man_days,
            "actual_man_days": self.actual_man_days,
            "scheduled_man_days": self.scheduled_man_days,
            "man_days_consumption": round(self.man_days_consumption, 2),
            "date_start": self.date_start,
            "date_deadline": self.date,
            "calendar_day_left": self.calendar_day_left,
            "calendar_progression": round(self.calendar_progression, 2),
            "budgeted_man_days": self.budgeted_man_days,
            "project_completion": round(self.project_completion, 2),
            "man_days_overconsumed": self.man_days_overconsumed,
            "performance": round(self.performance, 2),
            "performance_indicator_status": self.performance_indicator_status,
        }

    def _get_stat_buttons(self):
        buttons = super()._get_stat_buttons()
        buttons.append(
            {
                "icon": "history",
                "text": "Performances History",
                "number": len(self.project_performance_ids),
                "action_type": "object",
                "action": "action_open_project_performances",
                "show": len(self.project_performance_ids) > 0,
                "sequence": 80,
            }
        )
        return buttons

    def save_project_performance(self):
        project_perf_model = self.env["project.performance.history"]
        for project in self:
            values = project.get_performance_items()
            values["date"] = fields.Datetime.now()
            values["performance"] = values["performance"] / 100
            values["project_completion"] = values["project_completion"] / 100
            values["calendar_progression"] = values["calendar_progression"] / 100
            values["project_id"] = project.id
            project_perf_model.create(values)

    def action_open_project_performances(self):
        action = (
            self.env["ir.actions.act_window"]
            .with_context(active_id=self.id)
            ._for_xml_id("spantech_hr_timesheet.project_performance_action")
        )
        context = action["context"].replace("active_id", str(self.id))
        action["context"] = context
        return action

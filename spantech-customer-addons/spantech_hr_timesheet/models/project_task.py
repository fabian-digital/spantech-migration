# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare


class ProjectTack(models.Model):
    _inherit = "project.task"

    allow_timesheets = fields.Boolean(
        store=True,
        readonly=False,
    )
    timesheet_type = fields.Selection(
        selection=[
            ("installation", "Installation"),
            ("design", "Design"),
            ("production", "Production"),
        ],
        compute="_compute_timesheet_type",
        store=True,
    )

    allow_timesheets_project = fields.Boolean(
        related="project_id.allow_timesheets",
    )

    allocated_man_days = fields.Float(default=0)
    planned_hours = fields.Float(compute="_compute_planned_hours", store=True)

    employee_sponsor_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Sponsor",
    )

    man_day_spent = fields.Float(
        string="Man-Days Spent",
        compute="_compute_man_day_spent",
        store=True,
    )
    remaining_man_days = fields.Float(
        string="Remaining Man-Days",
        compute="_compute_remaining_man_days",
        store=True,
    )

    # rename field progress
    progress = fields.Float(string="Man-Days Consumption")

    task_completion = fields.Integer(
        help="The completion of the task in %",
        tracking=True,
    )

    performance_indicator = fields.Integer(
        compute="_compute_performance_indicator",
        store=True,
    )
    performance_indicator_status = fields.Selection(
        selection=[
            ("no", "No Man-Days"),
            ("good", "Good"),
            ("danger", "Danger"),
            ("bad", "Bad"),
        ],
        compute="_compute_performance_indicator",
        store=True,
    )
    performance_indicator_icon = fields.Html(
        compute="_compute_performance_indicator_icon",
    )

    _sql_constraints = [
        (
            "check_task_completion",
            "CHECK(task_completion BETWEEN 0 AND 100)",
            "Task Completion should be a number between 0 and 100.",
        ),
    ]

    def _compute_progress_hours(self):
        res = super()._compute_progress_hours()
        for task in self:
            # By default, Odoo stop at 100% event if the
            # task_total_hours is bigger than the task.planned_hours
            if task.planned_hours > 0.0:
                task_total_hours = task.effective_hours + task.subtask_effective_hours
                task.overtime = max(task_total_hours - task.planned_hours, 0)
                if (
                    float_compare(
                        task_total_hours, task.planned_hours, precision_digits=2
                    )
                    >= 0
                ):
                    task.progress = round(
                        100.0 * task_total_hours / task.planned_hours, 2
                    )
        return res

    def _compute_allow_timesheets(self):
        res = super()._compute_allow_timesheets()
        for task in self:
            task.allow_timesheets = False
        return res

    @api.depends("effective_hours", "project_id.hours_in_man_days")
    def _compute_man_day_spent(self):
        for task in self:
            if task.project_id.hours_in_man_days:
                task.man_day_spent = (
                    task.effective_hours / task.project_id.hours_in_man_days
                )
            else:
                task.man_day_spent = 0.0

    @api.depends("remaining_hours", "project_id.hours_in_man_days")
    def _compute_remaining_man_days(self):
        for task in self:
            if task.project_id.hours_in_man_days:
                task.remaining_man_days = (
                    task.remaining_hours / task.project_id.hours_in_man_days
                )
            else:
                task.remaining_man_days = 0.0

    @api.depends("allocated_man_days", "project_id.hours_in_man_days")
    def _compute_planned_hours(self):
        for task in self:
            task.planned_hours = (
                task.allocated_man_days * task.project_id.hours_in_man_days
            )

    @api.depends(
        "progress",
        "overtime",
        "task_completion",
        "project_id.task_completion_danger_threshold_min",
        "project_id.task_completion_danger_threshold_max",
    )
    def _compute_performance_indicator(self):
        for task in self:
            task.performance_indicator = task.task_completion - int(task.progress)
            if not int(task.progress):
                task.performance_indicator_status = "no"
            elif (
                task.performance_indicator
                < task.project_id.task_completion_danger_threshold_min
                or task.overtime
            ):
                task.performance_indicator_status = "bad"
            elif (
                task.performance_indicator
                <= task.project_id.task_completion_danger_threshold_max
            ):
                task.performance_indicator_status = "danger"
            elif (
                task.performance_indicator
                > task.project_id.task_completion_danger_threshold_max
            ):
                task.performance_indicator_status = "good"
            else:
                task.performance_indicator_status = "no"

    @api.depends("performance_indicator_status")
    def _compute_performance_indicator_icon(self):
        for task in self:
            if task.performance_indicator_status == "good":
                task.performance_indicator_icon = (
                    "<i class='fa fa-circle text-success'/>"
                )
            elif task.performance_indicator_status == "danger":
                task.performance_indicator_icon = (
                    "<i class='fa fa-circle text-warning'/>"
                )
            elif task.performance_indicator_status == "bad":
                task.performance_indicator_icon = (
                    "<i class='fa fa-circle text-danger'/>"
                )
            else:
                task.performance_indicator_icon = ""

    @api.depends("allow_timesheets")
    def _compute_timesheet_type(self):
        for task in self:
            task.timesheet_type = "installation" if task.allow_timesheets else False

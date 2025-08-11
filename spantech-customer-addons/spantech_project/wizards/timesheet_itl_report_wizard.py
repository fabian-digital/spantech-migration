# Copyright 2009-2024 Noviat
# The license_file.pdf file at the top level of
# this module contains the full copyright notices and license terms.


from odoo import api, fields, models


class TimesheetITLReportWizard(models.TransientModel):
    _name = "timesheet.itl.report.wizard"
    _description = "Timesheet ITL Report"

    project_ids = fields.Many2many(comodel_name="project.project")
    date = fields.Date(default=fields.Date.today)
    week_number = fields.Integer(compute="_compute_week_number")

    @api.depends("date")
    def _compute_week_number(self):
        self.week_number = self.date.isocalendar().week if self.date else 0

    def action_generate_report(self):
        ctx = dict(self.env.context)
        action = self.env["ir.actions.report"]._for_xml_id(
            "spantech_project.timesheet_itl_report_action"
        )
        action["context"] = ctx.update(
            {"active_ids": self.id, "active_model": "timesheet.itl.report.wizard"}
        )
        return action

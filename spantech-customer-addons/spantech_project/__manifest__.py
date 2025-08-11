# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech project",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "summary": " ",
    "depends": ["calendar", "project", "spantech_analytic", "project_enterprise"],
    "data": [
        "reports/timesheet_itl_report.xml",
        "security/ir.model.access.csv",
        "views/calendar_event_views.xml",
        "views/project_views.xml",
        "views/project_task_views.xml",
        "wizards/timesheet_itl_report_wizard_views.xml",
        "data/ir_actions_server.xml",
        "data/ir_rule.xml",
    ],
    "installable": True,
}

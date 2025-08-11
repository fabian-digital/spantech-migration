# Copyright 2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Hr Timesheet",
    "author": "Noviat",
    "license": "AGPL-3",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "version": "16.0.1.0.0",
    "depends": ["hr_timesheet", "project_account_budget"],
    "data": [
        "security/ir.model.access.csv",
        "views/project_performance_history_views.xml",
        "views/project_views.xml",
        "views/project_task.xml",
        "reports/project_task_summary_template.xml",
        "data/ir_cron.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "spantech_hr_timesheet/static/src/components/project_right_side_panel/**/*",
        ],
    },
    "installable": True,
}

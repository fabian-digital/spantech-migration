# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"

    spantech_type = fields.Selection(
        selection=[("project", "Project"), ("tag", "Tags")], default="project"
    )

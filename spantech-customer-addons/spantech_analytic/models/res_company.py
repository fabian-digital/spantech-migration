# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    is_analytic_percentage_limit = fields.Boolean(string="Analytic Limit")

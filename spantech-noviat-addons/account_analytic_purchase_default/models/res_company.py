# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    analytic_account_mandatory_on_purchase = fields.Boolean(
        string="Analytic Account Mandatory on Purchases",
    )

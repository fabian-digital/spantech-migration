# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    analytic_account_mandatory_on_invoice = fields.Boolean(
        related="company_id.analytic_account_mandatory_on_invoice",
        string="Analytic Account Mandatory on Invoices",
        readonly=False,
    )

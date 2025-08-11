# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    mrp_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get("mrp_analytic_account"):
            res["mrp_analytic_account_id"] = self.env.context["mrp_analytic_account"]
        return res

    def _prepare_run_values(self):
        values = super()._prepare_run_values()
        if self.mrp_analytic_account_id:
            values["analytic_account_id"] = self.mrp_analytic_account_id
        return values

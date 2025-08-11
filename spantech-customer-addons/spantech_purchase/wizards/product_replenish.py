# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ProductReplenish(models.TransientModel):
    _inherit = "product.replenish"

    purchase_analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
    )

    manufacturing = fields.Boolean(compute="_compute_manufacturing")

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        if self.env.context.get("purchase_analytic_account"):
            res["purchase_analytic_account_id"] = self.env.context[
                "purchase_analytic_account"
            ]
        return res

    @api.depends("route_ids")
    def _compute_manufacturing(self):
        for rec in self:
            try:
                if "Manufacture" in rec.route_ids.mapped("name"):
                    rec.manufacturing = True
                else:
                    rec.manufacturing = False
            except Exception:
                rec.manufacturing = False

    def _prepare_run_values(self):
        values = super()._prepare_run_values()
        if self.purchase_analytic_account_id:
            values["analytic_account_id"] = self.purchase_analytic_account_id
        return values

# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticPlan(models.Model):
    _inherit = "account.analytic.plan"
    _order = "sequence"

    sequence = fields.Integer(help="Determine the display order")

    @api.model
    def get_relevant_plans(self, **kwargs):
        res = super().get_relevant_plans(**kwargs)
        if len(res) > 0:
            planids = list(map(lambda k: k["id"], res))
            plan_ids = self.env["account.analytic.plan"].browse(planids)
            seqs = {elem.id: elem.sequence for elem in plan_ids}
            for item in res:
                item.update({"sequence": seqs[item["id"]]})
        return res

# Copyright 2009-2025 Noviat
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).


from odoo import _, models
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    def action_submit_expenses(self):
        for exp in self:
            if (
                exp.company_id.is_analytic_percentage_limit
                and exp.analytic_distribution
            ):
                if len(exp.analytic_distribution) > 1:
                    raise UserError(
                        _(
                            "Only one analytic account line is allowed. "
                            "Please check the lines!"
                        )
                    )
                for _analytic, value in exp.analytic_distribution.items():
                    if value != 100:
                        raise UserError(
                            _(
                                "The analytic lines should be set to 100%. "
                                "Please check the percentage of the analytic lines!"
                            )
                        )
        res = super().action_submit_expenses()
        return res

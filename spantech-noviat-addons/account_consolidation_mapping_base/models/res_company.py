# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (https://www.gnu.org/licenses/lpgl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class ResCompany(models.Model):
    _inherit = "res.company"

    consolidation_chart_id = fields.Many2one(
        string="Consolidation Chart",
        comodel_name="consolidation.chart",
        help="Select the Consolidation Chart to use for mapping purposes "
        "in this Company.",
    )

    def write(self, values):
        res = super().write(values)
        if "consolidation_chart_id" in values:
            for company in self:
                accounts = self.env["account.account"].search(
                    [("company_id", "=", company.id)]
                )
                for account in accounts:
                    consolidation_account_id = (
                        account.consolidation_account_ids.filtered(
                            lambda r, company=company: r.chart_id
                            == company.consolidation_chart_id
                        )
                    )
                    if len(consolidation_account_id) > 1:
                        raise UserError(
                            _(
                                "Consolidation Account configuration error:\n"
                                "Account %(account_code)s has been "
                                "mapped to multiple Consolidation "
                                "Accounts %(account_list)s "
                                "for Consolidation Chart '%(chart_name)'."
                            )
                            % {
                                "account_code": account.code,
                                "account_list": consolidation_account_id.mapped("code"),
                                "chart_name": company.consolidation_chart_id.name,
                            }
                        )
                    account.consolidation_account_id = consolidation_account_id
        return res

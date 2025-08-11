# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (https://www.gnu.org/licenses/lpgl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = "account.account"

    consolidation_account_id = fields.Many2one(
        comodel_name="consolidation.account",
        string="Consolidation Account",
        compute="_compute_consolidation_account_id",
        store=True,
    )

    @api.depends("consolidation_account_ids")
    def _compute_consolidation_account_id(self):
        for rec in self:
            consolidation_account_id = rec.consolidation_account_ids.filtered(
                lambda r, rec=rec: r.chart_id == rec.company_id.consolidation_chart_id
            )
            if len(consolidation_account_id) > 1:
                raise UserError(
                    _(
                        "Consolidation Account configuration error:\n"
                        "Account %(account_code)s "
                        "has been mapped to multiple Consolidation "
                        "Accounts %(account_list)s "
                        "for Consolidation Chart '%(chart_name)'."
                    )
                    % {
                        "account_code": rec.code,
                        "account_list": consolidation_account_id.mapped("code"),
                        "chart_name": rec.company_id.consolidation_chart_id.name,
                    }
                )
            rec.consolidation_account_id = consolidation_account_id

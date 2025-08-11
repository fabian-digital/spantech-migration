# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, models
from odoo.exceptions import UserError


class TrialBalanceReport(models.AbstractModel):
    _inherit = "report.account_financial_report.trial_balance"

    @api.model
    def _get_data(
        self,
        account_ids,
        journal_ids,
        partner_ids,
        company_id,
        date_to,
        date_from,
        foreign_currency,
        only_posted_moves,
        show_partner_details,
        hide_account_at_0,
        unaffected_earnings_account,
        fy_start_date,
    ):
        total_amount, accounts_data, partners_data = super()._get_data(
            account_ids,
            journal_ids,
            partner_ids,
            company_id,
            date_to,
            date_from,
            foreign_currency,
            only_posted_moves,
            show_partner_details,
            hide_account_at_0,
            unaffected_earnings_account,
            fy_start_date,
        )
        wiz_mod = self.env.context.get("active_model")
        wiz_id = self.env.context.get("active_id")
        wiz = self.env[wiz_mod].browse(wiz_id)

        if wiz.consolidation:
            for k in accounts_data:
                account = self.env["account.account"].browse(k)
                accounts_data[k]["consol_account"] = account.consolidation_account_id
                accounts_data[k]["consol_code"] = account.consolidation_account_id.code
        if wiz.consolidation != "replace":
            return total_amount, accounts_data, partners_data

        return self._get_data_consolidated(
            total_amount, accounts_data, partners_data, unaffected_earnings_account
        )

    def _get_data_consolidated(
        self, total_amount, accounts_data, partners_data, unaffected_earnings_account
    ):
        ca_total_amount = {}
        ca_data = {}
        for k in accounts_data:
            if k == unaffected_earnings_account:
                ca_data[k] = accounts_data[k]
                ca_total_amount[k] = total_amount[k]
                continue
            aa_data = accounts_data[k]
            ca = aa_data["consol_account"]
            if not ca:
                raise UserError(
                    _("Missing Consolidation Counterpart account for %s")
                    % aa_data["code"]
                )
            if ca.id not in ca_data:
                ca_data[ca.id] = {
                    "id": ca.id,
                    "code": ca.code,
                    "local_codes": aa_data["code"],
                    "name": ca.name,
                    "hide_account": aa_data["hide_account"],
                    "group_id": ca.group_id.id,
                    "currency_id": aa_data["currency_id"],
                    "currency_name": aa_data["currency_name"],
                    "centralized": aa_data["centralized"],
                }
            else:
                entry = ca_data[ca.id]
                if aa_data["code"] not in entry["local_codes"]:
                    entry["local_codes"] += ",{}".format(aa_data["code"])
                for fld in (
                    "hide_account",
                    "currency_id",
                    "currency_name",
                    "centralized",
                ):
                    if entry[fld] != aa_data[fld]:
                        raise UserError(
                            _(
                                "Error while checking field '%(field)s' "
                                "on Consolidation Account '%(account)s'."
                                "\nThis field is not consistent amongst the "
                                "consolidated local Accounts."
                                "\nThe logic to handle this has not been "
                                "implemented yet."
                            )
                            % {"field": fld, "account": ca.code}
                        )
            if ca.id not in ca_total_amount:
                ca_total_amount[ca.id] = {}
                for fld in total_amount[k]:
                    ca_total_amount[ca.id][fld] = total_amount[k][fld]
            else:
                for fld in total_amount[k]:
                    ca_total_amount[ca.id][fld] += total_amount[k][fld]
        return ca_total_amount, ca_data, partners_data

    def _get_groups_data(self, accounts_data, total_amount, foreign_currency):
        wiz_mod = self.env.context.get("active_model")
        wiz_id = self.env.context.get("active_id")
        wiz = self.env[wiz_mod].browse(wiz_id)
        if wiz.consolidation == "replace":
            raise UserError(
                _(
                    "Hierarchy reporting for Consolidated Trial Balance "
                    "is not yet implemented."
                )
            )
        return super()._get_groups_data(accounts_data, total_amount, foreign_currency)

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models


class GeneralLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.general_ledger"

    def _get_accounts_data(self, account_ids):
        res = super()._get_accounts_data(account_ids)
        for k in res:
            account = self.env["account.account"].browse(k)
            ccode = account.consolidation_account_id.code
            res[k]["consol_code"] = ccode
            if ccode:
                res[k]["code"] += " ({})".format(ccode)
        return res

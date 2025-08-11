# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class TrialBalanceXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_trial_balance_xlsx"

    def _get_report_columns(self, report):
        res = super()._get_report_columns(report)
        if report.consolidation == "add":
            ci = [k for k, v in res.items() if v["header"] == _("Code")]
            if ci:
                res2 = {k if k <= ci[0] else k + 1: v for k, v in res.items()}
                res2[ci[0] + 1] = {
                    "header": _("Cons. Code"),
                    "field": "consol_code",
                    "width": 10,
                }
                return res2
        elif report.consolidation == "replace":
            ci = [k for k, v in res.items() if v["header"] == _("Code")]
            if ci:
                res2 = {k if k <= ci[0] else k + 1: v for k, v in res.items()}
                res2[ci[0] + 1] = {
                    "header": _("Local Code(s)"),
                    "field": "local_codes",
                    "width": 20,
                }
                return res2
        return res

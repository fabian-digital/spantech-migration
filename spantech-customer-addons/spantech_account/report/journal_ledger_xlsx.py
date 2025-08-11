# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class JournalLedgerXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_journal_ledger_xlsx"

    def _get_report_columns(self, report):
        res = super()._get_report_columns(report)
        res.update(
            {len(res): {"field": "posting_user_id", "header": "Posted by", "width": 25}}
        )
        return res

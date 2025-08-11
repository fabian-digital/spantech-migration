# Copyright 2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class JournalLedgerReport(models.AbstractModel):
    _inherit = "report.account_financial_report.journal_ledger"

    def _get_move_lines_data(self, ml, wizard, ml_taxes, auto_sequence, exigible):
        res = super()._get_move_lines_data(
            ml, wizard, ml_taxes, auto_sequence, exigible
        )
        res.update({"posting_user_id": ml.move_id.posting_user_id.name})
        return res

# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class AccountPayment(models.Model):
    _inherit = "account.payment"

    def _seek_for_lines(self):
        liq_amls, cp_amls, writeoff_amls = super()._seek_for_lines()
        cp_amls |= self.move_id.line_ids.filtered(
            lambda r: r not in liq_amls
            and r.account_type in ("asset_current", "liability_current")
            and r.is_account_reconcile
        )
        return liq_amls, cp_amls, writeoff_amls

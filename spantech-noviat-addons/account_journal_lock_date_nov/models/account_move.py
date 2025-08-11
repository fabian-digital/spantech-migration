# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import date, timedelta

from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.returns("self", lambda value: value.id)
    def copy(self, default=None):
        """
        TODO:
        make PR to oca account_journal_lock_date_module to include this logic
        """
        default = dict(default or {})

        if self.user_has_groups("account.group_account_manager"):
            journal_lock_date = self.journal_id.fiscalyear_lock_date or date.min
        else:
            journal_lock_date = max(
                self.journal_id.period_lock_date or date.min,
                self.journal_id.fiscalyear_lock_date or date.min,
            )
        company_lock_date = self.company_id._get_user_fiscal_lock_date()
        lock_date = max(journal_lock_date, company_lock_date)
        if (fields.Date.to_date(default.get("date")) or self.date) <= lock_date:
            default["date"] = lock_date + timedelta(days=1)
        return super().copy(default=default)

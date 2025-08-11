# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError


class L10nBeLegalReport(models.TransientModel):
    _inherit = "l10n.be.legal.report"

    consolidation = fields.Boolean(help="Reporting on Consolidation Accounts:")

    def check_consolidation(self):
        """
        Check the consistency of the Consolidation Counterpart Account Settings.
        """
        accounts = self.env["account.account"].search(
            [("company_id", "=", self.company_id.id)], order="code"
        )
        self.env.cr.execute(
            """
        SELECT DISTINCT(account_id) FROM account_move_line
        WHERE date >= %s AND date <= %s
            """,
            (self.date_from or fields.Date.to_string(date.min), self.date_to),
        )
        res_ids = [x[0] for x in self.env.cr.fetchall()]
        accounts = accounts.filtered(lambda r: r.id in res_ids)
        missing = accounts.filtered(lambda r: not r.consolidation_account_id)
        if missing:
            msg = _("Missing Consolidation Counterpart account:")
            for ma in missing:
                msg += "\n%s" % ma.code
            raise UserError(msg)

        non_be_scheme_accounts = self.env["account.account"]
        be_scheme_entries = self.env["be.legal.financial.report.scheme"].search([])
        for account in accounts:
            conso = account.consolidation_account_id
            entry = be_scheme_entries.filtered(
                lambda r, conso=conso: r.account_group
                == conso.code[0 : len(r.account_group)]
            )
            if not entry:
                non_be_scheme_accounts += account
        if non_be_scheme_accounts:
            msg = _(
                "The Consolidation Account for the following accounts "
                "are not conform to the Belgian Balance and P&L reportscheme."
            )
            msg += "\n".join(x.code for x in non_be_scheme_accounts)
            raise UserError(msg)
        raise UserError(_("Sanity Check OK."))

    def _account_groups_filter(self, account, account_groups):
        for account_group in account_groups:
            if account_group == account.code[0 : len(account_group)]:
                return True
        return False

    def _get_chart_entry_domain(self, chart_entry, report_cache):
        if not self.consolidation:
            return super()._get_chart_entry_domain(chart_entry, report_cache)

        chart_schemes = report_cache["be_scheme_entries"].filtered(
            lambda r: r.report_chart_id == chart_entry
        )
        account_groups = chart_schemes.mapped("account_group")
        conso_accounts = (
            report_cache["accounts"]
            .mapped("consolidation_account_id")
            .filtered(lambda r: self._account_groups_filter(r, account_groups))
        )
        accounts = conso_accounts.mapped("account_ids")
        return [("account_id", "in", accounts.ids)]

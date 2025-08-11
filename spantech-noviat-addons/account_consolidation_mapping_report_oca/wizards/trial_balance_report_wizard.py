# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, fields, models
from odoo.exceptions import UserError


class TrialBalanceReportWizard(models.TransientModel):
    _inherit = "trial.balance.report.wizard"

    consolidation = fields.Selection(
        selection=[("add", "Add"), ("replace", "Replace")],
        help="Reporting on Consolidation Accounts:"
        "\n'None': standard report on local Chart Of Accounts."
        "\n'Add': Show Consolidation Counterpart Account Codes "
        "(only available in XLSX Export)."
        "\n'Replace': Replace local Chart of Accounts by "
        "Consolidation Chart of Accounts.",
    )

    def check_consolidation(self):
        """
        Check the consistency of the Consolidation Counterpart Account Settings.
        TODO:
        Extend check to accounts with initial balance != 0
        """
        missing = self.env["account.account"].search(
            [
                ("company_id", "=", self.company_id.id),
                ("consolidation_account_id", "=", False),
            ],
            order="code",
        )
        self.env.cr.execute(
            """
        SELECT DISTINCT(account_id) FROM account_move_line
        WHERE date >= %s AND date <= %s AND account_id IN %s
            """,
            (self.date_from, self.date_to, missing._ids),
        )
        res_ids = [x[0] for x in self.env.cr.fetchall()]
        if res_ids:
            missing = missing.filtered(lambda r: r.id in res_ids)
            msg = _("Missing Consolidation Counterpart account:")
            for m in missing:
                msg += "\n%s" % m.code
            raise UserError(msg)
        raise UserError(_("Sanity Check OK."))

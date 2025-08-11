# Copyright 2009-2020 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models


class AccountMoveLineXlsx(models.AbstractModel):
    _inherit = "report.account_move_line_report_xls.account_move_line_xlsx"

    def _get_col_specs(self):
        col_specs = super()._get_col_specs()
        col_specs["analytic_account_name"] = {
            "header": {"value": _("Analytic")},
            "lines": {"value": self._render("line.analytic_account_name")},
            "width": 40,
        }
        return col_specs

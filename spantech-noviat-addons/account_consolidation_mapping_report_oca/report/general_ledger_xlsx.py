# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class GeneralLedgerXslx(models.AbstractModel):
    _inherit = "report.a_f_r.report_general_ledger_xlsx"

    def write_line_from_dict(self, line_dict, report_data):
        line_dict["account"] = (
            line_dict["account"] and line_dict["account"].split(" (")[0]
        )
        return super().write_line_from_dict(line_dict, report_data)

# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

from odoo import models


class ReportPartnerLedger(models.AbstractModel):
    _inherit = "account.partner.ledger.report.handler"

    # TODO: UPDATE CODE
    # def _get_columns_name(self, options):
    #     columns = super()._get_columns_name(options)
    #     columns.insert(3, {"name": _("Move")})
    #     return columns
    #
    # @api.model
    # def _get_lines(self, options, line_id=None):
    #     lines = super()._get_lines(options, line_id=line_id)
    #     for line in lines:
    #         columns = line["columns"]
    #         if (
    #             line.get("level", 0) == 2
    #             and line.get("parent_id")
    #             and line.get("id", 0)
    #         ):
    #             aml = self.env["account.move.line"].browse(line.get("id"))
    #             columns[2].update({"name": aml.move_id.ref})
    #             columns.insert(2, {"name": aml.move_name})
    #             line.update({"columns": columns})
    #         elif (
    #             line.get("level", 0) == 2 or line.get("class", "") == "total"
    #         ) and line.get("colspan", 0):
    #             line.update({"colspan": line["colspan"] + 1})
    #     return lines

# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

from odoo import models


class AccountAgedReceivable(models.AbstractModel):
    _inherit = "account.aged.receivable.report.handler"

    # TODO: UPDATE CODE
    # def _get_columns_name(self, options):
    #     columns = super()._get_columns_name(options)
    #     columns.insert(
    #         5,
    #         {
    #             "name": _("Approver"),
    #             "class": "text-nowrap text-center",
    #         },
    #     )
    #     return columns
    #
    # @api.model
    # def _get_lines(self, options, line_id=None):
    #     lines = super()._get_lines(options, line_id=line_id)
    #     for line in lines:
    #         columns = line["columns"]
    #         if line.get("level", 0) == 2 and line.get("id", 0):
    #             aml = self.env["account.move.line"].browse(line.get("id"))
    #             columns.insert(4, {"name": aml.move_id.approver_id.name or ""})
    #             line.update({"columns": columns})
    #         elif (
    #             line.get("level", 0) == 1 or line.get("class", "") == "total"
    #         ) and line.get("colspan", 0):
    #             line.update({"colspan": line["colspan"] + 1})
    #     return lines

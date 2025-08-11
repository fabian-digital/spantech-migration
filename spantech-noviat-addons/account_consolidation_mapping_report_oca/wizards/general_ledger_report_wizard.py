# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class GeneralLedgerReportWizard(models.TransientModel):
    _inherit = "general.ledger.report.wizard"

    display_consolidation = fields.Boolean(
        default=True,
        help="Show Consolidation Counterpart Account Codes"
        "\nThis option is only effective when "
        "using the Excel Export.",
    )

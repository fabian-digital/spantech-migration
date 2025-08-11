# Copyright 2009-2024 Noviat
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class res_company(models.Model):
    _inherit = "res.company"

    intercompany_invoice_direction = fields.Selection(
        selection=[
            ("outbound", "Outbound"),
            ("inbound", "Inbound"),
            ("both", "Both"),
        ],
        string="Direction",
        default="both",
        required="True",
        help="Limit the creation of Intercompany Invoices to Outbound "
        "(Customer Invoice -> Vendor Bill) or Inbound "
        "(Vendor Bill -> Customer Invoice).",
    )

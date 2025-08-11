# Copyright 2009-2024 Noviat
# License LGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    intercompany_invoice_direction = fields.Selection(
        related="company_id.intercompany_invoice_direction", readonly=False
    )

    @api.depends("intercompany_invoice_direction")
    def _compute_intercompany_transaction_message(self):
        for rec in self:
            if (
                rec.rule_type == "invoice_and_refund"
                and rec.intercompany_invoice_direction != "both"
            ):
                if rec.intercompany_invoice_direction == "outbound":
                    src = _("an invoice")
                    dest = _("a bill")
                else:
                    src = _("a bill")
                    dest = _("an invoice")
                rec.intercompany_transaction_message = _(
                    "Generate %(dest)s when a company confirms %(src)s for %(cpy)s.",
                    dest=dest,
                    src=src,
                    cpy=rec.company_id.name,
                )
            else:
                super(
                    ResConfigSettings, rec
                )._compute_intercompany_transaction_message()
        return

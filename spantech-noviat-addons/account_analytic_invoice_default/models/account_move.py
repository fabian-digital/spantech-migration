# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    _name = "account.move"
    _inherit = ["account.move", "analytic.mixin"]

    @api.onchange("analytic_distribution")
    def _onchange_analytic_distribution(self):
        if self.analytic_distribution and self.invoice_line_ids:
            self.invoice_line_ids.analytic_distribution = self.analytic_distribution

    def action_post(self):
        for move in self:
            if (
                move.company_id.analytic_account_mandatory_on_invoice
                and move.move_type
                in ("out_invoice", "out_refund", "in_invoice", "in_refund")
            ):
                if any(
                    not line.analytic_distribution for line in move.invoice_line_ids
                ):
                    raise ValidationError(
                        _(
                            "The analytic distribution is mandatory for invoices. "
                            "Please define it before posting the invoice"
                        )
                    )
        return super().action_post()

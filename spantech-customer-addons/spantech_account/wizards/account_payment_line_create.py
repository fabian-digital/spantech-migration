# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountPaymentLineCreate(models.TransientModel):
    _inherit = "account.payment.line.create"

    invoice_approved = fields.Boolean(
        string="Invoice must be validated/approved", default=True
    )

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        context = self.env.context
        assert (
            context.get("active_model") == "account.payment.order"
        ), "active_model should be payment.order"
        assert context.get("active_id"), "Missing active_id in context !"
        order = self.env["account.payment.order"].browse(context["active_id"])
        mode = order.payment_mode_id
        res.update(
            {
                "invoice_approved": mode.default_invoice_approved,
            }
        )
        return res

    def _prepare_move_line_domain(self):
        self.ensure_one()
        domain = super()._prepare_move_line_domain()
        new_domain = []
        if self.invoice_approved:
            new_domain += [("move_id.validated", "=", True)]
        if self.order_id.payment_type == "outbound":
            for dom in domain:
                if dom[0] not in ["credit", "account_id.account_type"]:
                    new_domain.append(dom)
            new_domain += [
                ("credit", ">", 0),
                "|",
                ("move_id.is_spantech_prepayment", "=", True),
                (
                    "account_id.account_type",
                    "in",
                    ["asset_receivable", "liability_payable"],
                ),
            ]
        return new_domain

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    show_qty_in_percentage = fields.Boolean(
        string="Show Quantity in percentage in the invoice",
        default=lambda self: self._default_show_qty_in_percentage(),
    )

    partial_invoice = fields.Boolean()
    partial_invoice_percent = fields.Float()

    @api.model
    def _default_show_qty_in_percentage(self):
        if self.env.user.default_show_qty_in_percentage:
            return True
        else:
            return False

    @api.model
    def get_views(self, views, options=None):
        res = super().get_views(views, options)
        if (
            res.get("models")
            and res["models"].get(self._name)
            and res["models"][self._name].get("advance_payment_method")
            and res["models"][self._name]["advance_payment_method"].get("selection")
        ):
            res["models"][self._name]["advance_payment_method"]["selection"] = [
                ("delivered", "Regular invoice")
            ]
        return res

    def create_invoices(self):
        self = self.with_context(
            default_show_qty_in_percentage=self.show_qty_in_percentage
        )
        if self.partial_invoice:
            self = self.with_context(
                partial_invoice_percent=self.partial_invoice_percent
            )
        return super().create_invoices()

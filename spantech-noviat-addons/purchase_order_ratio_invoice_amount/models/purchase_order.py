# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import api, fields, models
from odoo.tools.misc import formatLang


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    invoiced_amount = fields.Monetary(
        compute="_compute_invoiced_amount",
        store=True,
        help="Order amount already invoiced.",
    )

    amount_invoiced_ratio_total = fields.Float(
        string="Invoiced Ratio",
        compute="_compute_amount_invoiced_ratio_total",
        store=True,
    )

    @api.depends(
        "state",
        "invoice_ids",
        "invoice_ids.amount_total_in_currency_signed",
        "amount_total",
        "invoice_ids.state",
    )
    def _compute_invoiced_amount(self):
        # Logic copy from module sale_order_invoice_amount
        for rec in self:
            if rec.state != "cancel" and rec.invoice_ids:
                rec.invoiced_amount = 0.0
                for invoice in rec.invoice_ids:
                    if invoice.state != "cancel":
                        if (
                            invoice.currency_id != rec.currency_id
                            and rec.currency_id != invoice.company_currency_id
                        ):
                            rec.invoiced_amount += invoice.currency_id._convert(
                                invoice.amount_total,
                                rec.currency_id,
                                invoice.company_id,
                                invoice.invoice_date or fields.Date.today(),
                            )
                        else:
                            rec.invoiced_amount += invoice.amount_total
            else:
                rec.invoiced_amount = 0.0

    @api.depends()
    def _compute_tax_totals(self):
        # logic copy from sale_order_invoice_amount to show the invoiced_amount in form view
        res = super()._compute_tax_totals()
        for order in self:
            lang_env = order.with_context(lang=order.partner_id.lang).env
            order.tax_totals.update(
                {
                    "invoiced_amount": order.invoiced_amount,
                    "formatted_invoiced_amount": formatLang(
                        lang_env, order.invoiced_amount, currency_obj=order.currency_id
                    ),
                }
            )
        return res

    @api.depends(
        "invoiced_amount",
        "amount_total",
    )
    def _compute_amount_invoiced_ratio_total(self):
        for sale in self:
            amount_invoiced_ratio_total = 0
            if sale.amount_total != 0.0:
                amount_invoiced_ratio_total = (
                    sale.invoiced_amount / sale.amount_total
                ) * 100
            sale.amount_invoiced_ratio_total = amount_invoiced_ratio_total

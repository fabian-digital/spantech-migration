# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.tools import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"

    @api.depends(
        "invoice_line_ids.currency_rate",
        "invoice_line_ids.tax_base_amount",
        "invoice_line_ids.tax_line_id",
        "invoice_line_ids.price_total",
        "invoice_line_ids.price_subtotal",
        "invoice_payment_term_id",
        "partner_id",
        "currency_id",
    )
    def _compute_tax_totals(self):
        super()._compute_tax_totals()
        for move in self:
            if move.company_id.country_id.code == "AE":
                move._set_subtotal_amount_company_currency()
                move._set_groups_by_subtotal_company_currency()
        return

    def _set_subtotal_amount_company_currency(self):
        self.ensure_one()
        if self.tax_totals:
            for subtotal in self.tax_totals.get("subtotals", []):
                subtotal_amount_company_currency = self.currency_id._convert(
                    subtotal["amount"],
                    self.company_currency_id,
                    self.company_id,
                    self.invoice_date or self.date,
                )
                subtotal["formatted_subtotal_amount_company_currency"] = formatLang(
                    self.env,
                    subtotal_amount_company_currency,
                    currency_obj=self.company_currency_id,
                )
        return

    def _set_groups_by_subtotal_company_currency(self):
        self.ensure_one()
        if self.tax_totals:
            for _key, value_list in self.tax_totals.get(
                "groups_by_subtotal", {}
            ).items():
                for values in value_list:
                    if "tax_group_amount" in values:
                        tax_group_base_amount_signed = self.currency_id._convert(
                            values["tax_group_amount"],
                            self.company_currency_id,
                            self.company_id,
                            self.invoice_date or self.date,
                        )
                        values[
                            "formatted_tax_group_base_amount_company_currency"
                        ] = formatLang(
                            self.env,
                            tax_group_base_amount_signed,
                            currency_obj=self.company_currency_id,
                        )

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.company_id.country_id.code == "AE":
            return "spantech_uae.report_invoice_document_far_east_limited"
        return super()._get_name_invoice_report()

    def _get_conversion_rate(self):
        self.ensure_one()
        conversion_rate = self.currency_id._get_conversion_rate(
            self.currency_id,
            self.company_currency_id,
            self.company_id,
            self.invoice_date or self.date,
        )
        return "1 {currency} = {rate} {company_currency}".format(
            currency=self.currency_id.name,
            rate=conversion_rate,
            company_currency=self.company_currency_id.name,
        )

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, models
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            if order.company_id.analytic_account_mandatory_on_sale:
                if not order.analytic_account_id:
                    raise ValidationError(
                        _(
                            "The analytic account is mandatory for sale orders. "
                            "Please define it before confirming the sales"
                        )
                    )
        return super().action_confirm()

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.analytic_account_id:
            res["analytic_distribution"] = {self.analytic_account_id.id: 100}
        return res

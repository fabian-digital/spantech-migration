# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _name = "purchase.order"
    _inherit = ["purchase.order", "analytic.mixin"]

    @api.onchange("analytic_distribution")
    def _onchange_analytic_distribution(self):
        if self.analytic_distribution and self.order_line:
            self.order_line.analytic_distribution = self.analytic_distribution

    def button_confirm(self):
        for po in self:
            if po.company_id.analytic_account_mandatory_on_purchase:
                if any(not line.analytic_distribution for line in po.order_line):
                    raise ValidationError(
                        _(
                            "The analytic distribution is mandatory for purchases. "
                            "Please define it before confirming the purchase"
                        )
                    )
        return super().button_confirm()

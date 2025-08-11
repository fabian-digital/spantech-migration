from odoo import api, fields, models


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="account_analytic_account_purchase_order_line_rel",
        column1="purchase_order_line_id",
        column2="analytic_account_id",
        compute="_compute_analytic_account_ids",
        store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        for line in self:
            if line.analytic_distribution:
                analytic_account_ids = [int(key) for key in line.analytic_distribution]
                line.analytic_account_ids = self.env["account.analytic.account"].browse(
                    analytic_account_ids
                )
            else:
                line.analytic_account_ids = False

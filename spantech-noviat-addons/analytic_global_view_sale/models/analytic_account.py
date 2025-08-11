from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    sale_order_ids = fields.One2many(
        inverse_name="analytic_account_id",
        comodel_name="sale.order",
        string="Sale Orders",
    )
    sale_order_ids_count = fields.Integer(
        compute="_compute_sale_order_ids_count",
    )
    sale_order_line_ids = fields.Many2many(
        comodel_name="sale.order.line",
        compute="_compute_sale_order_line_ids",
        store=True,
        compute_sudo=True,
    )

    @api.depends("sale_order_ids")
    def _compute_sale_order_ids_count(self):
        for analytic_account in self:
            if analytic_account.sale_order_ids:
                analytic_account.sale_order_ids_count = len(
                    analytic_account.sale_order_ids
                )
            else:
                analytic_account.sale_order_ids_count = 0

    @api.depends("sale_order_ids.analytic_account_id")
    def _compute_sale_order_line_ids(self):
        for analytic_account in self:
            if analytic_account.sale_order_ids:
                sale_lines = analytic_account.sale_order_ids.order_line
                analytic_account.sale_order_line_ids = sale_lines
            else:
                analytic_account.sale_order_line_ids = False

    def _compute_attachment_ids(self):
        res = super()._compute_attachment_ids()
        for analytic_account in self:
            attachments = analytic_account.attachment_ids
            attachment_ids_count = analytic_account.attachment_ids_count
            if analytic_account.sale_order_ids:
                sale_attachments = self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "sale.order"),
                        ("res_id", "in", analytic_account.sale_order_ids.ids),
                    ]
                )
                attachments |= sale_attachments
                attachment_ids_count += len(sale_attachments)
            analytic_account.attachment_ids = attachments
            analytic_account.attachment_ids_count = attachment_ids_count
        return res

    def action_open_sale_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action.update(
            {"domain": [("id", "in", self.sale_order_ids.ids)], "context": {}}
        )
        return action

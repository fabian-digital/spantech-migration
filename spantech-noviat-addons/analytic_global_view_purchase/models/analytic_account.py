from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    purchase_order_line_ids = fields.Many2many(
        comodel_name="purchase.order.line",
        relation="account_analytic_account_purchase_order_line_rel",
        column1="analytic_account_id",
        column2="purchase_order_line_id",
        string="Purchase Order Lines",
    )
    purchase_order_ids = fields.Many2many(
        comodel_name="purchase.order",
        compute="_compute_purchase_order_ids",
        store=True,
        compute_sudo=True,
    )
    purchase_order_ids_count = fields.Integer(
        compute="_compute_purchase_order_ids_count",
    )

    @api.depends("purchase_order_line_ids")
    def _compute_purchase_order_ids(self):
        for analytic_account in self:
            if analytic_account.purchase_order_line_ids:
                purchase_lines = analytic_account.purchase_order_line_ids.mapped(
                    "order_id"
                )
                analytic_account.purchase_order_ids = purchase_lines
            else:
                analytic_account.purchase_order_ids = False

    @api.depends("purchase_order_ids")
    def _compute_purchase_order_ids_count(self):
        for analytic_account in self:
            if analytic_account.purchase_order_ids:
                analytic_account.purchase_order_ids_count = len(
                    analytic_account.purchase_order_ids
                )
            else:
                analytic_account.purchase_order_ids_count = 0

    def _compute_attachment_ids(self):
        res = super()._compute_attachment_ids()
        for analytic_account in self:
            attachments = analytic_account.attachment_ids
            attachment_ids_count = analytic_account.attachment_ids_count
            if analytic_account.purchase_order_ids:
                purchase_attachments = self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "purchase.order"),
                        ("res_id", "in", analytic_account.purchase_order_ids.ids),
                    ]
                )
                attachments |= purchase_attachments
                attachment_ids_count += len(purchase_attachments)
            analytic_account.attachment_ids = attachments
            analytic_account.attachment_ids_count = attachment_ids_count
        return res

    def action_open_purchase_orders(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "purchase.purchase_form_action"
        )
        action.update(
            {"domain": [("id", "in", self.purchase_order_ids.ids)], "context": {}}
        )
        return action

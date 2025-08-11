from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    account_move_line_ids = fields.Many2many(
        comodel_name="account.move.line",
        relation="account_analytic_account_account_move_line_rel",
        column1="account_analytic_account_id",
        column2="account_move_line_id",
        string="Account Move Lines",
    )
    account_move_ids = fields.Many2many(
        comodel_name="account.move",
        compute_sudo=True,
        compute="_compute_account_move_ids",
        store=True,
    )
    account_move_ids_count = fields.Integer(
        compute="_compute_account_move_ids_count",
    )
    attachment_ids = fields.Many2many(
        comodel_name="ir.attachment",
        compute="_compute_attachment_ids",
    )
    attachment_ids_count = fields.Integer(
        compute="_compute_attachment_ids",
    )

    @api.depends("account_move_line_ids")
    def _compute_account_move_ids(self):
        for analytic_account in self:
            if analytic_account.account_move_line_ids:
                move_ids = analytic_account.account_move_line_ids.mapped("move_id")
                analytic_account.account_move_ids = move_ids
            else:
                analytic_account.account_move_ids = False

    @api.depends("account_move_ids")
    def _compute_account_move_ids_count(self):
        for analytic_account in self:
            if analytic_account.account_move_ids:
                analytic_account.account_move_ids_count = len(
                    analytic_account.account_move_ids
                )
            else:
                analytic_account.account_move_ids_count = 0

    @api.depends("account_move_ids")
    def _compute_attachment_ids(self):
        for analytic_account in self:
            if analytic_account.account_move_ids:
                attachments = self.env["ir.attachment"].search(
                    [
                        ("res_model", "=", "account.move"),
                        ("res_id", "in", analytic_account.account_move_ids.ids),
                    ]
                )
                analytic_account.attachment_ids = attachments
                analytic_account.attachment_ids_count = len(attachments)
            else:
                analytic_account.attachment_ids_count = 0

    def action_open_account_moves(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "account.action_move_line_form"
        )
        action.update(
            {"domain": [("id", "in", self.account_move_ids.ids)], "context": {}}
        )
        return action

    def action_open_attachments(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_attachment")
        action.update(
            {"domain": [("id", "in", self.attachment_ids.ids)], "context": {}}
        )
        return action

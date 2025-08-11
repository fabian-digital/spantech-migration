# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        store=True,
    )
    project_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="account_analytic_account_account_move_project_rel",
        compute="_compute_analytic_account_ids",
        store=True,
        string="Analytic by Project",
    )
    tag_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        relation="account_analytic_account_account_move_tag_rel",
        compute="_compute_analytic_account_ids",
        store=True,
        string="Analytic by Tag",
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        for move in self:
            if move.analytic_distribution:
                acc_ids = self.env["account.analytic.account"].browse(
                    [int(k) for k in move.analytic_distribution]
                )
                move.analytic_account_ids = acc_ids
                move.project_analytic_account_ids = acc_ids.filtered(
                    lambda ac: ac.plan_id and ac.plan_id.spantech_type == "project"
                )
                move.tag_analytic_account_ids = acc_ids.filtered(
                    lambda ac: ac.plan_id and ac.plan_id.spantech_type == "tag"
                )
            else:
                move.analytic_account_ids = False
                move.project_analytic_account_ids = False
                move.tag_analytic_account_ids = False

    @api.onchange("analytic_account_ids")
    def _onchange_approver_id(self):
        for move in self:
            if move.analytic_account_ids:
                for analytic in move.analytic_account_ids:
                    if analytic.approver_id:
                        move.approver_id = analytic.approver_id.id
                        break

    def action_post(self):
        for move in self:
            if move.company_id.is_analytic_percentage_limit:
                for line in move.line_ids.filtered(lambda ln: ln.analytic_distribution):
                    for _analytic, value in line.analytic_distribution.items():
                        if value != 100:
                            raise UserError(
                                _(
                                    "The analytic lines should be set to 100%. "
                                    "Please check the percentage of the analytic lines!"
                                )
                            )
        res = super().action_post()
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner", store=True, related="move_id.commercial_partner_id"
    )

    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        store=True,
    )
    project_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        relation="account_analytic_account_account_move_line_project_rel",
        store=True,
        string="Analytic by Project",
    )
    tag_analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        relation="account_analytic_account_account_line_tag_rel",
        store=True,
        string="Analytic by Tag",
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        for line in self:
            if line.analytic_distribution:
                acc_ids = self.env["account.analytic.account"].browse(
                    [int(k) for k in line.analytic_distribution]
                )
                line.analytic_account_ids = acc_ids
                line.project_analytic_account_ids = acc_ids.filtered(
                    lambda ac: ac.plan_id and ac.plan_id.spantech_type == "project"
                )
                line.tag_analytic_account_ids = acc_ids.filtered(
                    lambda ac: ac.plan_id and ac.plan_id.spantech_type == "tag"
                )
            else:
                line.analytic_account_ids = False
                line.project_analytic_account_ids = False
                line.tag_analytic_account_ids = False

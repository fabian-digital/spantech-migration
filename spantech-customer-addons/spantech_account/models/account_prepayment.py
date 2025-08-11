# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountPrepaymentSpantech(models.Model):
    _name = "account.prepayment.spantech"
    _description = "Account Prepayment - Spantech"
    _order = "prepayment_date desc, name desc, id desc"
    _check_company_auto = True
    _inherit = ["mail.thread", "mail.activity.mixin", "tier.validation"]
    _state_from = ["confirm", "posted"]
    _state_to = ["posted"]

    _tier_validation_manual_config = False

    name = fields.Char(compute="_compute_name", store=True)
    move_id = fields.Many2one(
        comodel_name="account.move",
        string="Move",
        readonly=1,
        copy=False,
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        store=True,
        readonly=True,
        compute="_compute_company_id",
    )
    partner_id = fields.Many2one(
        comodel_name="res.partner",
        readonly=True,
        tracking=True,
        states={"draft": [("readonly", False)]},
        check_company=True,
        string="Vendor",
        required=1,
    )
    journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Journal",
        check_company=True,
        tracking=True,
        default=lambda self: self._default_journal_id(),
        required=1,
        readonly=1,
        states={"draft": [("readonly", False)]},
        domain=[("type", "=", "purchase")],
    )
    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        check_company=True,
        tracking=True,
        readonly=1,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
    )
    ref = fields.Char(string="Reference", tracking=True)
    partner_bank_id = fields.Many2one(
        comodel_name="res.partner.bank",
        string="Vendor Bank Account",
        check_company=True,
        tracking=True,
        readonly=1,
        required=1,
        states={
            "draft": [("readonly", False)],
        },
    )
    prepayment_date = fields.Date(
        required=True,
        index=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        copy=False,
        default=fields.Date.context_today,
    )
    approver_id = fields.Many2one(
        comodel_name="res.users",
        string="Approver",
        tracking=True,
        states={"draft": [("readonly", False)], "confirm": [("readonly", False)]},
    )
    currency_id = fields.Many2one(
        comodel_name="res.currency",
        store=True,
        readonly=True,
        tracking=True,
        required=True,
        states={"draft": [("readonly", False)]},
        string="Currency",
        default=lambda self: self._default_currency_id(),
    )
    prepayment_amount = fields.Monetary(
        tracking=True,
        readonly=True,
        states={"draft": [("readonly", False)]},
        currency_field="currency_id",
        required=1,
    )
    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        check_company=True,
        tracking=True,
        default=lambda self: self._default_payment_mode_id(),
    )
    state = fields.Selection(
        copy=False,
        selection=[
            ("draft", "Draft"),
            ("confirm", "Confirmed"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
        default="draft",
        tracking=True,
    )
    user_id = fields.Many2one(
        comodel_name="res.users",
        copy=False,
        tracking=True,
        string="User",
        default=lambda self: self.env.user,
    )
    expected_vendor_bill_receipt_date = fields.Date(
        copy=False,
        string="Estimated Vendor Bill Date",
        help="Estimated date of receipt of supplier bill",
    )
    payment_state = fields.Selection(
        string="Payment Status",
        related="move_id.payment_state",
        store=True,
    )
    matched_status = fields.Selection(
        string="Matched",
        related="move_id.matched_status",
        store=True,
    )

    @api.model
    def _default_journal_id(self):
        if self.env.company.prepayment_journal_id:
            return self.env.company.prepayment_journal_id.id
        else:
            return self.env["account.journal"]

    @api.model
    def _default_payment_mode_id(self):
        if self.env.company.prepayment_payment_mode_id:
            return self.env.company.prepayment_payment_mode_id.id
        else:
            return self.env["account.payment.mode"]

    @api.model
    def _default_currency_id(self):
        journal = self.env.company.prepayment_journal_id
        return journal.currency_id.id or journal.company_id.currency_id.id

    @api.depends("move_id")
    def _compute_name(self):
        for prepayment in self:
            if prepayment.move_id:
                prepayment.name = prepayment.move_id.name
            elif prepayment.state == "confirm":
                prepayment.name = "Confirmed Prepayment"
            elif prepayment.state == "cancel":
                prepayment.name = "Cancelled Prepayment"
            else:
                prepayment.name = "Draft Prepayment"

    @api.depends("journal_id")
    def _compute_company_id(self):
        for move in self:
            move.company_id = (
                move.journal_id.company_id or move.company_id or self.env.company
            )

    @api.depends("approver_id", "payment_state")
    def _compute_can_restart_validation(self):
        for prepayment in self:
            if self.env.user.has_group("account.group_account_manager"):
                prepayment.can_restart_validation = True
            elif (
                self.env.user in (prepayment.approver_id, prepayment.user_id)
                and prepayment.state != "posted"
                and (
                    prepayment.payment_state == "not_paid"
                    or not prepayment.payment_state
                )
            ):
                prepayment.can_restart_validation = True
            else:
                prepayment.can_restart_validation = False

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        self = self.with_company(self.journal_id.company_id)
        bank_ids = self.partner_id.bank_ids.filtered(
            lambda bank: bank.company_id is False or bank.company_id == self.company_id
        )
        self.partner_bank_id = bank_ids and bank_ids[0]

    @api.onchange("analytic_account_id", "partner_id")
    def _onchange_approver_id(self):
        if self.analytic_account_id and self.analytic_account_id.approver_id:
            self.approver_id = self.analytic_account_id.approver_id
        elif self.partner_id and self.partner_id.approver_id:
            self.approver_id = self.partner_id.approver_id

    def action_confirm(self):
        self.ensure_one()
        self.write({"state": "confirm"})

    def action_post(self):
        self.ensure_one()
        if not self.move_id:
            move = self._create_account_move()
            self.write({"state": "posted", "move_id": move.id})
        else:
            raise UserError(
                _("You can not post a prepayment that is already related to a move.")
            )

    def action_draft(self):
        self.ensure_one()
        self.write({"state": "draft"})

    def action_cancel(self):
        self.ensure_one()
        self.write({"state": "cancel"})

    def action_open_reconciled_tree(self):
        return self.move_id.action_open_reconciled_tree()

    def _create_account_move(self):
        self.ensure_one()
        credit_move_line_values = {
            "amount_currency": -self.prepayment_amount,
            "partner_id": self.partner_id.id,
            "product_id": self.env.ref(
                "spantech_account.product_product_vendor_prepayment"
            ).id,
            "currency_id": self.currency_id.id,
            "account_id": self.env.ref(
                "spantech_account.product_product_vendor_prepayment"
            ).property_account_expense_id.id,
        }

        debit_move_line_values = {
            "amount_currency": self.prepayment_amount,
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "account_id": self.partner_id.property_account_payable_id.id,
        }
        move_values = {
            "move_type": "entry",
            "is_spantech_prepayment": True,
            "journal_id": self.journal_id.id,
            "payment_mode_id": self.payment_mode_id.id,
            "date": self.prepayment_date,
            "currency_id": self.currency_id.id,
            "partner_bank_id": self.partner_bank_id.id,
            "ref": self.ref,
            "line_ids": [
                (0, 0, credit_move_line_values),
                (0, 0, debit_move_line_values),
            ],
        }
        if self.analytic_account_id:
            analytic_distribution = {self.analytic_account_id.id: 100}
            credit_move_line_values["analytic_distribution"] = analytic_distribution
            move_values["analytic_distribution"] = analytic_distribution
        move = self.env["account.move"].new(move_values)
        move = self.env["account.move"].create(move._convert_to_write(move._cache))
        if self.review_ids:
            review_values = {"res_id": move.id, "model": "account.move"}
            tiers = self.env["tier.definition"].search([("model", "=", move._name)])
            for tier in tiers:
                if move.evaluate_tier(tier):
                    review_values["definition_id"] = tier.id
                    break
            self.review_ids.write(review_values)
        move.action_post()
        return move

    def request_validation(self):
        for prepayment in self:
            user_ids = self.env.user.partner_id.ids
            if prepayment.approver_id:
                user_ids += prepayment.approver_id.partner_id.ids
            prepayment.with_context(
                mail_thread_allow_auto_followers=True
            ).message_subscribe(partner_ids=user_ids)
        return super().request_validation()

    def unlink(self):
        for record in self:
            if record.move_id:
                raise UserError(
                    _(
                        "You can not delete a prepayment which is already "
                        "link to an Account Move"
                    )
                )
            if record.state not in ("cancel", "draft"):
                raise UserError(
                    _("Only a cancelled or draft prepayment can be " "deleted")
                )
        return super().unlink()

    @api.model
    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res += [
            "message_main_attachment_id",
        ]
        return res

    def _get_to_validate_message_name(self):
        return "Account Prepayment"

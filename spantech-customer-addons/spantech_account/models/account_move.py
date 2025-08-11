# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.misc import formatLang


class AccountMove(models.Model):
    _inherit = "account.move"
    _state_from = ["draft", "posted"]
    _state_to = ["posted"]

    date = fields.Date(string="Accounting Date")
    invoice_date = fields.Date(default=lambda self: self._default_invoice_date())
    posting_date = fields.Date(copy=False)
    posting_user_id = fields.Many2one(comodel_name="res.users", string="Posted By")
    approver_id = fields.Many2one(comodel_name="res.users", string="Approver")
    show_qty_in_percentage = fields.Boolean(
        string="Show Quantity in percentage",
        default=lambda self: self._default_show_qty_in_percentage(),
    )
    is_spantech_prepayment = fields.Boolean(string="Spantech Prepayment")
    has_reconciled_entries = fields.Boolean(store=True)
    expected_vendor_bill_receipt_date = fields.Date(
        string="Estimated Vendor Bill Date",
        help="Estimated date of receipt of supplier bill",
    )
    matched_status = fields.Selection(
        selection=[
            ("not_matched", "Not Matched"),
            ("partial_matched", "Partial Matched"),
            ("full_matched", "Fully Matched"),
        ],
        string="Matched",
        compute="_compute_matched_status",
        store=True,
    )

    show_reference_in_document = fields.Boolean(
        string="Show Reference in Document", default=False
    )
    show_analytic_in_document = fields.Boolean(
        string="Show Analytic Code line by line in Document", default=False
    )
    last_payment_date = fields.Date(compute="_compute_last_payment_date")

    @api.model
    def _default_show_qty_in_percentage(self):
        if self.env.user.default_show_qty_in_percentage and self.env.context.get(
            "default_move_type"
        ) in ("out_invoice", "out_refund"):
            return True
        else:
            return False

    @api.model
    def _default_invoice_date(self):
        return (
            fields.Date.context_today(self)
            if self._context.get("default_move_type", "entry")
            in self.get_purchase_types(include_receipts=True)
            else False
        )

    @api.depends("move_type", "line_ids.amount_residual")
    def _compute_last_payment_date(self):
        for move in self:
            latest_date = False
            if move.invoice_payments_widget and move.invoice_payments_widget.get(
                "content", False
            ):
                for line in move.invoice_payments_widget["content"]:
                    if not line.get("is_exchange"):
                        if not latest_date or line.get("date") > latest_date:
                            latest_date = line.get("date")
            move.last_payment_date = latest_date

    @api.depends("move_type")
    def _compute_payment_mode_filter_type_domain(self):
        super()._compute_payment_mode_filter_type_domain()
        for move in self:
            if move.is_spantech_prepayment:
                move.payment_mode_filter_type_domain = "outbound"
        return

    @api.depends("partner_id", "payment_mode_id")
    def _compute_partner_bank_id(self):
        super()._compute_partner_bank_id()
        for move in self:
            # No bank account assignation is done for out_invoice as this is only
            # needed for printing purposes and it can conflict with
            # SEPA direct debit payments. Current report prints it.
            def get_bank_id(mv):
                return mv.commercial_partner_id.bank_ids.filtered(
                    lambda b, m=mv: b.company_id == m.company_id or not b.company_id
                )[:1]

            bank_id = False
            if move.partner_id:
                if move.move_type == "in_invoice":
                    if (
                        move.commercial_partner_id.bank_ids
                        and len(move.commercial_partner_id.bank_ids) < 2
                    ):
                        bank_id = get_bank_id(move)
                    move.partner_bank_id = bank_id
        return

    @api.depends(
        "line_ids",
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
        "line_ids.full_reconcile_id",
    )
    def _compute_has_reconciled_entries(self):
        return super()._compute_has_reconciled_entries()

    @api.depends(
        "has_reconciled_entries",
        "line_ids",
        "line_ids.matched_debit_ids",
        "line_ids.matched_credit_ids",
        "line_ids.full_reconcile_id",
    )
    def _compute_matched_status(self):
        for move in self:
            if (
                move.has_reconciled_entries
                and move.invoice_payments_widget
                and move.invoice_payments_widget.get("content", False)
            ):
                if all(
                    move_line.reconciled
                    for move_line in move.line_ids.filtered(
                        lambda ml: ml.account_type
                        in ("liability_payable", "asset_receivable")
                        or (
                            ml.display_type == "product"
                            and ml.move_id.is_spantech_prepayment
                        )
                    )
                ):
                    move.matched_status = "full_matched"
                else:
                    move.matched_status = "partial_matched"
            else:
                move.matched_status = "not_matched"

    def _compute_amount(self):
        super()._compute_amount()
        for move in self.filtered(lambda m: m.is_spantech_prepayment):
            reconciled_lines = move.line_ids.filtered(
                lambda line: line.account_type
                not in ("asset_receivable", "liability_payable")
            )
            if all(move_line.reconciled for move_line in reconciled_lines):
                move.payment_state = "paid"
        return

    @api.depends("move_type", "line_ids.amount_residual")
    def _compute_payments_widget_reconciled_info(self):
        super()._compute_payments_widget_reconciled_info()
        for move in self.filtered(lambda m: m.is_spantech_prepayment):
            payments_widget_vals = {
                "title": _("Less Payment"),
                "outstanding": False,
                "content": [],
            }

            if move.state == "posted" and move.is_spantech_prepayment:
                reconciled_vals = []
                reconciled_partials = move._get_all_reconciled_invoice_partials()
                for reconciled_partial in reconciled_partials:
                    counterpart_line = reconciled_partial["aml"]
                    if counterpart_line.move_id.ref:
                        reconciliation_ref = (
                            f"{counterpart_line.move_id.name} "
                            f"{counterpart_line.move_id.ref}"
                        )
                    else:
                        reconciliation_ref = counterpart_line.move_id.name
                    if (
                        counterpart_line.amount_currency
                        and counterpart_line.currency_id
                        != counterpart_line.company_id.currency_id
                    ):
                        foreign_currency = counterpart_line.currency_id
                    else:
                        foreign_currency = False
                    method_name = (
                        counterpart_line.payment_id.payment_method_line_id.name
                    )
                    reconciled_vals.append(
                        {
                            "name": counterpart_line.name,
                            "journal_name": counterpart_line.journal_id.name,
                            "amount": reconciled_partial["amount"],
                            "currency_id": move.company_id.currency_id.id
                            if reconciled_partial["is_exchange"]
                            else reconciled_partial["currency"].id,
                            "date": counterpart_line.date,
                            "partial_id": reconciled_partial["partial_id"],
                            "account_payment_id": counterpart_line.payment_id.id,
                            "payment_method_name": method_name,
                            "move_id": counterpart_line.move_id.id,
                            "ref": reconciliation_ref,
                            "is_exchange": reconciled_partial["is_exchange"],
                            "amount_company_currency": formatLang(
                                self.env,
                                abs(counterpart_line.balance),
                                currency_obj=counterpart_line.company_id.currency_id,
                            ),
                            "amount_foreign_currency": foreign_currency
                            and formatLang(
                                self.env,
                                abs(counterpart_line.amount_currency),
                                currency_obj=foreign_currency,
                            ),
                        }
                    )
                payments_widget_vals["content"] = reconciled_vals
            if payments_widget_vals["content"]:
                move.invoice_payments_widget = payments_widget_vals
            else:
                move.invoice_payments_widget = False
        return

    @api.depends("approver_id", "payment_state")
    def _compute_can_restart_validation(self):
        for move in self:
            if self.env.user.has_group("account.group_account_manager"):
                move.can_restart_validation = True
            elif self.env.user in (move.approver_id, move.user_id) and (
                move.payment_state == "not_paid" or not move.payment_state
            ):
                move.can_restart_validation = True
            else:
                move.can_restart_validation = False

    @api.onchange("partner_id", "commercial_partner_id")
    def _onchange_approver_id(self):
        if self.commercial_partner_id and self.commercial_partner_id.approver_id:
            self.approver_id = self.commercial_partner_id.approver_id

    @api.depends("move_type", "partner_id")
    def _compute_journal_id(self):
        not_processed_moves = self
        for move in self:
            if move.partner_id:
                if (
                    move.move_type in ("in_invoice", "in_refund")
                    and move.commercial_partner_id.property_in_journal_id
                ):
                    move.journal_id = move.commercial_partner_id.property_in_journal_id
                    not_processed_moves -= move
                elif (
                    move.move_type in ("out_invoice", "out_refund")
                    and move.commercial_partner_id.property_out_journal_id
                ):
                    move.journal_id = move.commercial_partner_id.property_out_journal_id
                    not_processed_moves -= move
        return super(AccountMove, not_processed_moves)._compute_journal_id()

    def action_post(self):
        for move in self:
            if move.is_spantech_prepayment:
                self = self.with_context(force_write_under_validation=True)
        self.write(
            {
                "posting_date": fields.Date.today(),
                "posting_user_id": self.env.user.id,
            }
        )
        return super().action_post()

    def action_open_reconciled_tree(self):
        self.ensure_one()
        reconciled_vals = self.invoice_payments_widget
        values = {"move_id": self.id, "line_ids": []}
        if reconciled_vals and reconciled_vals.get("content", False):
            for reconciled_val in reconciled_vals["content"]:
                values["line_ids"].append(
                    (
                        0,
                        0,
                        {
                            "journal_name": reconciled_val["journal_name"],
                            "amount": reconciled_val["amount"],
                            "move_id": reconciled_val["move_id"],
                            "date": reconciled_val["date"],
                            "payment_id": reconciled_val["account_payment_id"],
                            "currency_id": self.currency_id.id,
                        },
                    )
                )
        move_tree_reconciled = self.env["account.move.tree.reconciled"].create(values)
        view_id = self.env.ref(
            "spantech_account.account_move_tree_reconciled_view_form"
        ).id
        return {
            "type": "ir.actions.act_window",
            "name": _("Reconciliation Informations"),
            "view_mode": "form",
            "res_model": "account.move.tree.reconciled",
            "target": "new",
            "res_id": move_tree_reconciled.id,
            "views": [[view_id, "form"]],
        }

    def request_validation(self):
        for move in self:
            user_ids = self.env.user.partner_id.ids
            if move.approver_id:
                user_ids += move.approver_id.partner_id.ids
            move.with_context(mail_thread_allow_auto_followers=True).message_subscribe(
                partner_ids=user_ids
            )
        return super().request_validation()

    def create_account_payment_line(self):
        for move in self:
            if not move.validated:
                raise UserError(_("The invoice %s is not validated") % move.name)
        return super().create_account_payment_line()

    @api.model
    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res += [
            "amount_untaxed",
            "amount_tax",
            "amount_total",
            "amount_residual",
            "amount_untaxed_signed",
            "amount_tax_signed",
            "amount_total_signed",
            "amount_residual_signed",
            "payment_state",
            "payment_mode_filter_type_domain",
            "message_main_attachment_id",
            "l10n_de_tax_statement_id",
        ]
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    price_unit = fields.Float(digits="Account Move Product Price")
    is_prepayment_line = fields.Boolean(string="Prepayment Line")
    purchase_price_total = fields.Float(
        string="Total Cost",
        compute="_compute_purchase_price_total",
        store=True,
        digits="Product Price",
    )
    analytic_account_name = fields.Char(compute="_compute_analytic_account_name")
    amount_currency = fields.Monetary(
        group_operator="sum",
    )
    posting_date = fields.Date(related="move_id.posting_date", store=True)
    posting_user_id = fields.Many2one(related="move_id.posting_user_id", store=True)

    @api.depends("move_id.payment_mode_id", "move_id.is_spantech_prepayment")
    def _compute_payment_mode(self):
        super()._compute_payment_mode()
        for line in self:
            if line.move_id.is_spantech_prepayment:
                line.payment_mode_id = line.move_id.payment_mode_id
        return

    @api.depends("purchase_price", "quantity")
    def _compute_purchase_price_total(self):
        for move_line in self:
            if move_line.purchase_price and move_line.quantity:
                move_line.purchase_price_total = (
                    move_line.quantity * move_line.purchase_price
                )
            else:
                move_line.purchase_price_total = 0.0

    def _compute_analytic_account_name(self):
        for line in self:
            analytic_names = []
            if line.analytic_distribution:
                analytic_account_ids = [
                    int(acc_id) for acc_id in line.analytic_distribution.keys()
                ]
                if analytic_account_ids:
                    analytic_accounts = self.env["account.analytic.account"].browse(
                        analytic_account_ids
                    )
                    analytic_names = analytic_accounts.mapped("name")
            line.analytic_account_name = ",".join(analytic_names)

    @api.model
    def _report_xlsx_fields(self):
        columns = super()._report_xlsx_fields()
        columns.extend(
            [
                "analytic_account_name",
                "amount_residual",
                "currency_name",
                "amount_currency",
                "amount_residual_currency",
            ]
        )
        return columns

    # TODO Find new entry point
    # def _create_exchange_difference_move(self, exchange_diff_vals):
    #     exchange_move = super()._create_exchange_difference_move(exchange_diff_vals)
    #     if exchange_move:
    #         origin_move = self.filtered(
    #             lambda aml: aml.move_id and aml.move_id.invoice_origin
    #         )
    #         if origin_move:
    #             exchange_move.write(
    #                 {
    #                     "invoice_origin": origin_move[0].move_id.invoice_origin,
    #                     "ref": origin_move[0].move_id.name,
    #                 }
    #             )
    #     return exchange_move

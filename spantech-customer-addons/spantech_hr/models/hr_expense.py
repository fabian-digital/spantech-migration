# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrExpense(models.Model):
    _inherit = "hr.expense"

    expense_mandatory_attachment = fields.Boolean(
        string="Expense - Mandatory receipt",
        related="product_id.expense_mandatory_attachment",
    )
    expense_journal_id = fields.Many2one(
        comodel_name="account.journal",
        string="Payment Mode",
        check_company=True,
        tracking=True,
    )
    expense_journal_id_domain = fields.Binary(
        string="Journal Domain", compute="_compute_jounal_id_domain"
    )
    allow_create_expense_report = fields.Boolean(
        related="employee_id.allow_create_expense_report", store=True
    )
    attachment_ids = fields.One2many(
        comodel_name="ir.attachment",
        inverse_name="res_id",
        domain=[("res_model", "=", "hr.expense")],
        string="Attachments",
    )
    first_attachment_datas = fields.Binary(
        compute="_compute_first_attachment", string="Attachment", store=True
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        Analytic = self.env["account.analytic.account"]
        for exp in self:
            if exp.analytic_distribution:
                acc_ids = Analytic.browse([int(k) for k in exp.analytic_distribution])
                exp.analytic_account_ids = acc_ids
            else:
                exp.analytic_account_ids = False

    @api.depends("employee_id", "payment_mode")
    def _compute_jounal_id_domain(self):
        for expense in self:
            domain = [("is_spantech_expense", "=", True)]
            if expense.employee_id and expense.employee_id.allowed_expense_journal_ids:
                domain += [
                    ("id", "in", expense.employee_id.allowed_expense_journal_ids.ids)
                ]
            elif (
                expense.employee_id
                and expense.employee_id.company_id.expense_journal_id
            ):
                domain += [
                    ("id", "!=", expense.employee_id.company_id.expense_journal_id.id)
                ]
            expense.expense_journal_id_domain = domain

    @api.depends("product_id", "attachment_number", "currency_rate")
    def _compute_unit_amount(self):
        for expense in self.filtered("product_id"):
            current_unit_amount = expense.unit_amount
            super(HrExpense, expense)._compute_unit_amount()
            if (
                current_unit_amount
                and current_unit_amount != expense.unit_amount
                or not expense.unit_amount
            ):
                expense.unit_amount = current_unit_amount
        return

    @api.depends("attachment_ids")
    def _compute_first_attachment(self):
        for expense in self:
            if expense.attachment_ids:
                expense.first_attachment_datas = expense.attachment_ids[0].datas

    def _compute_is_editable(self):
        for rec in self:
            if rec.sheet_id.state == "review":
                rec.is_editable = True
            else:
                super(HrExpense, rec)._compute_is_editable()
        return

    def action_get_attachment_view(self):
        self.ensure_one()
        res = super().action_get_attachment_view()
        if self.attachment_number == 1:
            res["views"] = [(False, "form")]
            res["res_id"] = self.attachment_ids[0].id
        return res

    def action_submit_expenses(self):
        if any(
            expense.expense_mandatory_attachment and not expense.attachment_number
            for expense in self
        ):
            raise UserError(
                _("You cannot add a expense without an attachment/receipt!")
            )
        return super().action_submit_expenses()

    def _get_default_expense_sheet_values(self):
        values = []
        employee_sheet = self.filtered(
            lambda sheet: sheet.payment_mode == "own_account"
        )
        company_sheet = self.filtered(
            lambda sheet: sheet.payment_mode == "company_account"
        )
        if company_sheet:
            for journal_id in company_sheet.mapped("expense_journal_id"):
                journal_expenses = company_sheet.filtered(
                    lambda pe, j=journal_id: pe.expense_journal_id == j
                )
                if journal_expenses:
                    vals = super(
                        HrExpense,
                        journal_expenses,
                    )._get_default_expense_sheet_values()
                    for val in vals:
                        val["bank_journal_id"] = journal_id.id
                        values.append(val)
        if employee_sheet:
            vals = super(
                HrExpense,
                employee_sheet,
            )._get_default_expense_sheet_values()
            for val in vals:
                val["journal_id"] = self.company_id.expense_journal_id.id
                val["payment_mode_id"] = self.company_id.expense_payment_mode_id.id
                values.append(val)
        return values

    def update_expense(self):
        view = self.env.ref("spantech_hr.hr_expense_update_wizard_view_form")
        ctx = dict(
            self.env.context,
            default_exp_line_id=self.id,
            default_product_id=self.product_id.id,
            default_account_id=self.account_id.id,
            default_tax_ids=self.tax_ids.ids,
            default_analytic_distribution=self.analytic_distribution,
            default_company_id=self.company_id.id,
        )
        return {
            "name": _("Update Expense"),
            "view_type": "form",
            "view_mode": "form",
            "res_model": "hr.expense.update.wizard",
            "view_id": view.id,
            "target": "new",
            "type": "ir.actions.act_window",
            "context": ctx,
        }


class HrExpenseSheet(models.Model):
    _inherit = "hr.expense.sheet"

    state = fields.Selection(
        selection_add=[("review", "To Review"), ("submit",)],
        ondelete={"review": "set submit"},
    )
    payment_mode_id = fields.Many2one(
        comodel_name="account.payment.mode",
        string="Payment mode",
    )
    journal_id = fields.Many2one(domain=[("is_spantech_expense", "=", True)])
    bank_journal_id = fields.Many2one(domain=[("is_spantech_expense", "=", True)])
    cashwithdrawal_move_id = fields.Many2one(
        comodel_name="account.move", string="Cash Withdrawal Entry"
    )
    validation_amount = fields.Monetary(currency_field="currency_id", tracking=True)
    allow_submit_expense_report = fields.Boolean(
        related="employee_id.allow_submit_expense_report", store=True
    )
    show_submit_button = fields.Boolean(compute="_compute_show_submit_button")

    @api.depends("employee_id")
    def _compute_show_submit_button(self):
        for sheet in self:
            if (
                sheet.employee_id.user_id == self.env.user
                and not sheet.employee_id.allow_submit_expense_report
            ):
                sheet.show_submit_button = False
            else:
                sheet.show_submit_button = True

    def action_submit_sheet(self):
        for expense_sheet in self:
            if any(
                expense.expense_mandatory_attachment and not expense.attachment_number
                for expense in expense_sheet.expense_line_ids
            ):
                raise UserError(
                    _("You cannot submit a expense without an attachment/receipt!")
                )
            if (
                not expense_sheet.validation_amount
                or expense_sheet.validation_amount != expense_sheet.total_amount
            ):
                raise UserError(
                    _(
                        "The validation amount is empty or is different "
                        "from the calculated total amount !"
                    )
                )

            reviewer = expense_sheet.employee_id.expense_reviewer_id.user_id
            if not reviewer or expense_sheet.state == "review":
                super(HrExpenseSheet, expense_sheet).action_submit_sheet()
            else:
                expense_sheet.state = "review"
        return

    def action_sheet_move_create(self):
        move_group_by_sheet = super().action_sheet_move_create()
        for sheet in self:
            if any(
                expense.product_id.is_expense_cashwithdrawal
                for expense in sheet.expense_line_ids
            ):
                cashwithdrawals = {}
                for expense in sheet.expense_line_ids.filtered(
                    lambda e: e.product_id.is_expense_cashwithdrawal
                ):
                    if expense.account_id.id not in cashwithdrawals:
                        cashwithdrawals[expense.account_id.id] = expense.total_amount
                    else:
                        cashwithdrawals[expense.account_id.id] = (
                            cashwithdrawals[expense.account_id.id]
                            + expense.total_amount
                        )
                if cashwithdrawals:
                    move_values = sheet._prepare_cashwithdrawal_move_values()
                    move_lines = []
                    for (
                        cashwithdrawal_account_id,
                        cashwithdrawal_total_amount,
                    ) in cashwithdrawals.items():
                        move_line_credit_values = (
                            sheet._prepare_cashwithdrawal_move_line_values(
                                -cashwithdrawal_total_amount, cashwithdrawal_account_id
                            )
                        )
                        move_line_debit_values = (
                            sheet._prepare_cashwithdrawal_move_line_values(
                                cashwithdrawal_total_amount,
                                sheet.bank_journal_id.default_account_id.id,
                            )
                        )
                        move_lines += [
                            (0, 0, move_line_credit_values),
                            (0, 0, move_line_debit_values),
                        ]
                    move_values["line_ids"] = move_lines
                    move_cashwithdrawal = self.env["account.move"].new(move_values)
                    sheet.cashwithdrawal_move_id = self.env["account.move"].create(
                        move_cashwithdrawal._convert_to_write(
                            move_cashwithdrawal._cache
                        )
                    )
                    sheet.cashwithdrawal_move_id._post()

                    for cashwithdrawal_acc_id in cashwithdrawals.keys():
                        move_lines_to_reconcile = self.env["account.move.line"]
                        for move in move_group_by_sheet:
                            move_lines_to_reconcile |= move.line_ids.filtered(
                                lambda m, cwa=cashwithdrawal_acc_id: m.account_id.id
                                == cwa
                            )
                        move_lines_to_reconcile |= (
                            sheet.cashwithdrawal_move_id.line_ids.filtered(
                                lambda m, cwa=cashwithdrawal_acc_id: m.account_id.id
                                == cwa
                            )
                        )
                        move_lines_to_reconcile.reconcile()
                else:
                    raise UserError(
                        _(
                            "Expense Report used some Cash Withdrawal "
                            "products but something is missing (Account or Amount)"
                        )
                    )
        return move_group_by_sheet

    def _prepare_cashwithdrawal_move_values(self):
        return {
            "move_type": "entry",
            "date": self.accounting_date,
            "journal_id": self.bank_journal_id.id,
        }

    def _prepare_cashwithdrawal_move_line_values(self, amount, account_id):
        return {
            "partner_id": self.employee_id.address_home_id.id,
            "account_id": account_id,
            "amount_currency": amount,
            "currency_id": self.currency_id.id,
        }

    def _prepare_move_vals(self):
        vals = super()._prepare_move_vals()
        if self.payment_mode_id:
            vals["payment_mode_id"] = self.payment_mode_id.id
        return vals

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class HrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"

    allowed_expense_journal_domain = fields.Binary(
        string="Journal Domain", compute="_compute_allowed_expense_journal_domain"
    )
    allowed_expense_journal_ids = fields.Many2many(
        comodel_name="account.journal",
        relation="allowed_expense_account_journal_hr_employee_rel",
        column1="hr_employee_id",
        column2="account_journal_id",
        string="Allowed Expense Payment Modes",
    )
    allow_submit_expense_report = fields.Boolean(
        string="Allow to submit the expenses reports"
    )
    allow_create_expense_report = fields.Boolean(
        string="Allow to create the expenses reports"
    )
    expense_reviewer_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Expense Reviewer",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id), ('id', '!=', id)]",  # noqa: E501
        help="Select the user responsible for a sanity check of the Expense Notes "
        "before assigning it to his manager for approval.",
    )

    @api.depends("company_id")
    def _compute_allowed_expense_journal_domain(self):
        for employee in self:
            domain = [("is_spantech_expense", "=", True)]
            if employee.company_id.expense_journal_id:
                domain += [("id", "!=", employee.company_id.expense_journal_id.id)]
            employee.allowed_expense_journal_domain = domain

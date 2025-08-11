# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class AccountBankStatement(models.Model):
    _inherit = "account.bank.statement"

    employee_id = fields.Many2one(comodel_name="hr.employee", string="Employee")
    address_home_id = fields.Many2one(
        comodel_name="res.partner",
        string="Employee Partner",
        compute_sudo=True,
        compute="_compute_address_home_id",
    )
    is_spantech_expense = fields.Boolean(
        string="Expense Journal", related="journal_id.is_spantech_expense", store=True
    )

    @api.depends("employee_id")
    def _compute_address_home_id(self):
        for statement in self:
            if statement.employee_id and statement.employee_id.address_home_id:
                statement.address_home_id = statement.employee_id.address_home_id.id
            else:
                statement.address_home_id = False

    def action_update_partner_based_on_employee(self):
        self.ensure_one()
        if self.employee_id:
            self.line_ids.update({"partner_id": self.employee_id.address_home_id.id})

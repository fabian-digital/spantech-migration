from odoo import fields, models


class AccountAnalyticAccountState(models.Model):
    _name = "account.analytic.account.state"
    _description = "State for Analytic Accounts"
    _order = "sequence, name, id"

    name = fields.Char(required=True, translate=True)
    sequence = fields.Integer(default=1, help="Used to order states.")
    fold = fields.Boolean(
        "Folded in Kanban", help="This state is folded in the kanban view."
    )

    _sql_constraints = [
        (
            "account_analytic_account_state_name_unique",
            "unique(name)",
            "State name already exists",
        )
    ]

# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class AccountMoveTreeReconciled(models.TransientModel):
    _name = "account.move.tree.reconciled"
    _description = "Summary wizard for reconciliations"

    line_ids = fields.One2many(
        comodel_name="account.move.tree.reconciled.line",
        inverse_name="account_move_tree_reconciled_id",
    )
    move_id = fields.Many2one(comodel_name="account.move", string="Move")


class AccountMoveTreeReconciledLine(models.TransientModel):
    _name = "account.move.tree.reconciled.line"
    _description = "Lines for summary wizard for reconciliations"

    account_move_tree_reconciled_id = fields.Many2one(
        comodel_name="account.move.tree.reconciled"
    )
    journal_name = fields.Char(string="Journal")
    amount = fields.Monetary(currency_field="currency_id")
    date = fields.Date(string="Reconciliation Date")
    move_id = fields.Many2one(comodel_name="account.move", string="Reconciliation Move")
    payment_id = fields.Many2one(comodel_name="account.payment", string="Payment")
    currency_id = fields.Many2one(comodel_name="res.currency", string="Currency")

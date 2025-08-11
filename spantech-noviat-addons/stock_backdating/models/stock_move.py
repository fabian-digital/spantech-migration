# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _action_done(self, cancel_backorder=False):
        moves_todo = super()._action_done()
        for move in moves_todo:
            force_date = False
            if move.picking_id and move.picking_id.force_date:
                force_date = move.picking_id.force_date
            elif self.env.context.get("force_date"):
                force_date = self.env.context.get("force_date")
            if force_date:
                move.write({"date": force_date})
                for move_line in move.move_line_ids:
                    move_line.write({"date": force_date})
        return moves_todo

    def _prepare_account_move_vals(
        self,
        credit_account_id,
        debit_account_id,
        journal_id,
        qty,
        description,
        svl_id,
        cost,
    ):
        vals = super()._prepare_account_move_vals(
            credit_account_id,
            debit_account_id,
            journal_id,
            qty,
            description,
            svl_id,
            cost,
        )
        move_date = vals["date"]
        if self.env.context.get("force_period_date"):
            move_date = self.env.context.get("force_period_date")
        elif self.picking_id.force_date:
            move_date = self.picking_id.force_date
        elif self.env.context.get("force_date"):
            move_date = self.env.context.get("force_date")
        vals["date"] = move_date
        return vals

# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    cancel_reason = fields.Text(tracking=True)

    def action_cancel(self):
        if self.env.context.get("cancel_reason"):
            return {
                "type": "ir.actions.act_window",
                "name": _("Cancel MO"),
                "view_mode": "form",
                "res_model": "cancel.reason.wizard",
                "target": "new",
            }
        return super().action_cancel()

    def action_confirm(self):
        for order in self:
            if not order.analytic_account_id:
                raise UserError(
                    _(
                        "The analytic account is mandatory to confirm a "
                        "manufacturing order"
                    )
                )
            # Set analytic account to components moves and finished product moves.
            # This will transfer it to the related move lines afterward.
            order.move_raw_ids.write(
                {"analytic_distribution": {order.analytic_account_id.id: 100}}
            )
            order.move_finished_ids.write(
                {"analytic_distribution": {order.analytic_account_id.id: 100}}
            )
        if self.env.context.get("manual_confirmation", False):
            super().action_confirm()
        else:
            return False

    def action_progress(self):
        if not self.analytic_account_id:
            raise UserError(
                _("The analytic account is mandatory to start a manufacturing order")
            )
        return super().action_progress()

    def button_mark_done(self):
        if not self.force_date:
            raise UserError(
                _(
                    "A Production Date must be specified in order to "
                    "complete this manufacturing order"
                )
            )

        return super().button_mark_done()

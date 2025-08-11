# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class CancelReasonWizard(models.Model):
    _name = "cancel.reason.wizard"
    _description = "Cancel Reason Wizard"

    cancel_reason = fields.Text()

    def cancel_order(self):
        orders = self.env["mrp.production"].browse(
            self.env.context.get("active_ids", [])
        )
        orders.cancel_reason = self.cancel_reason
        orders.with_context(cancel_reason=False).action_cancel()

# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    def _routing_warn(self, error_message, message_id, route, raise_exception=True):
        if (
            route
            and route[0] == "res.users"
            and self.env.context.get("fetchmail_cron_running", False)
        ):
            return super()._routing_warn(
                error_message, message_id, route, raise_exception=False
            )
        else:
            return super()._routing_warn(error_message, message_id, route)

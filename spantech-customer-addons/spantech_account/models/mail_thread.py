# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.returns("mail.message", lambda value: value.id)
    def message_post(self, *args, **kwargs):
        if kwargs.get("partner_ids", False) and self.env.context.get(
            "add_additionnal_partner_message", False
        ):
            kwargs["partner_ids"] += self.env.context.get(
                "add_additionnal_partner_message"
            )
        return super().message_post(*args, **kwargs)

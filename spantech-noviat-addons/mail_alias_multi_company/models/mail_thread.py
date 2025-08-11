# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def _routing_check_route(self, message, message_dict, route, raise_exception=True):
        res = super()._routing_check_route(
            message, message_dict, route, raise_exception=raise_exception
        )
        if res:
            alias = route[4]
            if alias and isinstance(alias, models.BaseModel):
                to = message_dict["to"].lower() if "to" in message_dict else ""
                alias_mail = "{}@{}".format(alias.alias_name, alias.alias_domain)
                if to and alias_mail and alias_mail in to:
                    return res
                else:
                    return False
        return res

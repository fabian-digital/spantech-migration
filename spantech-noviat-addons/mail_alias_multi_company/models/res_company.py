# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    mail_alias_domain = fields.Char(
        default=lambda self: self._default_mail_alias_domain()
    )

    @api.model
    def _default_mail_alias_domain(self):
        return self.env["ir.config_parameter"].get_param("mail.catchall.domain")

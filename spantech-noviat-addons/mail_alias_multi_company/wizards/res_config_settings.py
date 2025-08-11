# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    mail_alias_domain = fields.Char(
        related="company_id.mail_alias_domain",
        string="Mail Alias Domain",
        readonly=False,
    )

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    dummy_project_maximum_amount = fields.Float(
        related="company_id.dummy_project_maximum_amount",
        string="Dummy Project Maximum Amount",
        readonly=False,
    )

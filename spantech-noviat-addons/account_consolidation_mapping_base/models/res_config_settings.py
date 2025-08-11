# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    consolidation_chart_id = fields.Many2one(
        related="company_id.consolidation_chart_id",
        readonly=False,
    )

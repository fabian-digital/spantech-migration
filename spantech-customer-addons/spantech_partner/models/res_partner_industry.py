# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartnerIndustry(models.Model):
    _inherit = "res.partner.industry"

    full_name = fields.Char(compute="_compute_full_name", store=True)

    segment = fields.Char()
    subsegment = fields.Char()

    @api.depends("subsegment", "segment")
    def _compute_full_name(self):
        for industry in self:
            full_name = ""
            if industry.segment:
                full_name += industry.segment.upper() + " / "
            if industry.subsegment:
                full_name += industry.subsegment.upper()
            industry.full_name = full_name

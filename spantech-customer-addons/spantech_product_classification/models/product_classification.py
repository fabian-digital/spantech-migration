# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models


class ProductClassification(models.Model):
    _inherit = "product.classification"

    @api.model
    def default_get(self, fields_list):
        self = self.with_context(default_company_id=None)
        return super().default_get(fields_list)

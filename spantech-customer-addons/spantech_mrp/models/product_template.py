# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    total_mo_count = fields.Integer(
        string="Production Frequency",
        compute="_compute_total_mo_count",
        store=True,
    )

    @api.depends("product_variant_ids", "product_variant_ids.total_mo_count")
    def _compute_total_mo_count(self):
        for product in self:
            product.total_mo_count = sum(
                p.total_mo_count for p in product.product_variant_ids
            )

# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    production_ids = fields.One2many(
        comodel_name="mrp.production",
        inverse_name="product_id",
        string="Production Orders",
    )

    total_mo_count = fields.Integer(
        string="Production Frequency",
        compute="_compute_total_mo_count",
        store=True,
    )

    @api.depends("production_ids", "production_ids.state")
    def _compute_total_mo_count(self):
        for product in self:
            product.total_mo_count = len(
                product.production_ids.filtered(lambda p: p.state in ["done"])
            )

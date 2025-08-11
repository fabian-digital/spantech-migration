# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models
from odoo.http import request


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    def download_plans(self):
        prod_attach = self.env["ir.attachment"]
        for pl in self.order_line:
            if pl.product_id:
                domain = [
                    ("name", "=like", f"{pl.product_id.default_code[:7]}%"),
                    "|",
                    "&",
                    ("res_model", "=", "product.product"),
                    ("res_id", "=", pl.product_id.id),
                    "&",
                    ("res_model", "=", "product.template"),
                    ("res_id", "=", pl.product_id.product_tmpl_id.id),
                ]
                prod_attach += self.env["ir.attachment"].search(domain)
        if len(prod_attach) > 0:
            ids = ",".join(map(str, prod_attach.ids))
            url = f"{request.httprequest.host_url}web/attachment/download_zip?ids={ids}"
            return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "self",
            }


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    @api.model
    def _prepare_purchase_order_line_from_procurement(
        self, product_id, product_qty, product_uom, company_id, values, po
    ):
        vals = super()._prepare_purchase_order_line_from_procurement(
            product_id, product_qty, product_uom, company_id, values, po
        )
        if values.get("group_id", False):
            group_id = values.get("group_id")
            if group_id.sale_id and group_id.sale_id.analytic_account_id:
                vals["analytic_distribution"] = {
                    group_id.sale_id.analytic_account_id.id: 100
                }
        return vals

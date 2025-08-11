# Part of Odoo. See LICENSE file for full copyright and licensing details.


from odoo import models


class ReplenishmentReport(models.AbstractModel):
    _inherit = "report.stock.report_product_product_replenishment"

    def _prepare_report_line(
        self,
        quantity,
        move_out=None,
        move_in=None,
        replenishment_filled=True,
        product=False,
        reservation=False,
    ):
        res = super()._prepare_report_line(
            quantity, move_out, move_in, replenishment_filled, product, reservation
        )
        document_in_origin = False
        document_out_origin = False
        if res.get("document_in", False):
            if res["document_in"]._name == "purchase.order":
                document_in_origin = res["document_in"].partner_ref
            elif res["document_in"]._name == "mrp.production":
                document_in_origin = res["document_in"].origin
        if res.get("document_out", False):
            if res["document_out"]._name == "sale.order":
                document_out_origin = res["document_out"].client_order_ref
            elif res["document_out"]._name == "mrp.production":
                document_out_origin = res["document_out"].origin
        res["document_in_origin"] = document_in_origin
        res["document_out_origin"] = document_out_origin
        return res

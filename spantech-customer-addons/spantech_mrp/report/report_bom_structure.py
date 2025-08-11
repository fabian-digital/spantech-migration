# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import io
import logging
from base64 import b64decode, b64encode

from pdf2image import convert_from_bytes

from odoo import api, models

_logger = logging.getLogger(__name__)


class ReportBomStructure(models.AbstractModel):
    _inherit = "report.mrp.report_bom_structure"
    _description = "BOM Structure Report"

    @api.model
    def _get_pdf_doc(self, bom_id, data, quantity, product_variant_id=None):
        doc = super()._get_pdf_doc(bom_id, data, quantity, product_variant_id)
        if not doc.get("warehouse", False) and data.get("warehouse_id"):
            if not isinstance(data["warehouse_id"], int):
                warehouse_id = int(data["warehouse_id"])
            else:
                warehouse_id = data["warehouse_id"]
            doc["warehouse"] = self.env["stock.warehouse"].browse(warehouse_id)
        if product_variant_id:
            product = self.env["product.product"].browse(product_variant_id)
            plan = self._get_plan(product)
            if plan:
                try:
                    doc["plans"].insert(0, self._get_plan_image(plan))
                except Exception as exc:
                    _logger.error(exc)
        return doc

    @api.model
    def _get_bom_array_lines(
        self, data, level, unfolded_ids, unfolded, parent_unfolded=True
    ):
        lines = super()._get_bom_array_lines(
            data=data,
            level=level,
            unfolded_ids=unfolded_ids,
            unfolded=unfolded,
            parent_unfolded=parent_unfolded,
        )
        # Add the prod_id in the lines to be able to search the product plan on the
        # _get_pdf_line method
        bom_lines = data["components"]
        for bom_line in bom_lines:
            line_dict = next(
                item
                for item in lines
                if item["name"] == bom_line["name"] and not item.get("prod_id", False)
            )
            line_dict["prod_id"] = bom_line["product_id"]
        return lines

    def _get_pdf_line(  # pylint: disable=W0102
        self,
        bom_id,
        product_id=False,
        qty=1,
        unfolded_ids=[],  # noqa: B006
        unfolded=False,
    ):
        data = super()._get_pdf_line(bom_id, product_id, qty, unfolded_ids, unfolded)
        plans = {}
        for line in data["lines"]:
            if "prod_id" in line:
                product_id = self.env["product.product"].browse(line["prod_id"])
                plan = self._get_plan(product_id)
                if not plans.get(line["prod_id"], False):
                    try:
                        plans[line["prod_id"]] = self._get_plan_image(plan)
                    except Exception as exc:
                        _logger.error(exc)
        data["plans"] = list(plans.values())
        return data

    # FIX because the method _has_attachments in the mrp module does not return a
    # boolean if the attachment is in the main product (not in components)
    @api.model
    def _has_attachments(self, data):
        res = super()._has_attachments(data)
        return bool(res)

    @api.model
    def _get_plan(self, product):
        return self.env["mrp.document"].search(
            [
                "|",
                "&",
                ("res_model", "=", "product.product"),
                ("res_id", "=", product.id),
                "&",
                ("res_model", "=", "product.template"),
                ("res_id", "=", product.product_tmpl_id.id),
                "|",
                ("mimetype", "=ilike", "image%"),
                ("mimetype", "=ilike", "%/pdf"),
            ],
            limit=1,
        )

    @api.model
    def _get_plan_image(self, plan):
        image = {}
        landscape = plan.image_height <= plan.image_width or False
        if "/pdf" in plan.mimetype:
            file_bytes = b64decode(plan.ir_attachment_id.datas, validate=True)
            images = convert_from_bytes(file_bytes, fmt="jpeg")
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format="jpeg")
            img_byte_arr = img_byte_arr.getvalue()
            image["plan_src"] = b64encode(img_byte_arr)
        else:
            image["plan_src"] = plan.ir_attachment_id.datas
        image["plan_landscape"] = landscape
        return image

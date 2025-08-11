# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def create(self, vals):
        if vals.get("res_model", False) == "product.product":
            tmpl_id = self.env["product.product"].browse(vals["res_id"]).product_tmpl_id
            vals["res_model"] = "product.template"
            vals["res_id"] = tmpl_id.id
        res = super().create(vals)
        if not self.env.context.get("mrp_document", False):
            if res["res_model"] == "product.template":
                tmpl_id = self.env["product.template"].browse(vals["res_id"])
                if (
                    tmpl_id.default_code
                    and tmpl_id.default_code in res["name"].split(".")[0]
                ):
                    self.env["mrp.document"].create({"ir_attachment_id": res.id})
        return res

    def sync_existing_ir_attachment_mrp_attachment(self):
        attachments = self.env["ir.attachment"].search(
            [
                ("res_model", "=", "product.template"),
            ]
        )
        mrp_documents = self.env["mrp.document"].search(
            [("ir_attachment_id", "in", attachments.ids)]
        )
        attachments = attachments - mrp_documents.mapped("ir_attachment_id")
        for attach in attachments:
            tmpl_id = self.env[attach.res_model].browse(attach.res_id)
            if (
                tmpl_id.default_code
                and attach.name
                and tmpl_id.default_code in attach.name
            ):
                self.env["mrp.document"].create({"ir_attachment_id": attach.id})

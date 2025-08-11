# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductProduct(models.Model):
    _inherit = "product.product"

    secondary_code = fields.Char(copy=False)

    def button_bom_cost(self):
        if not self.user_has_groups("spantech_product.group_edit_product_cost"):
            raise UserError(
                _(
                    "You don't have the access right to update cost. "
                    "Please contact your Manager."
                )
            )
        return super().button_bom_cost()

    def _get_mail_thread_data_attachments(self):
        self.ensure_one()
        res = super()._get_mail_thread_data_attachments()
        product_template_attachments = self.env["ir.attachment"].search(
            [
                ("res_id", "in", self.product_tmpl_id.ids),
                ("res_model", "=", "product.template"),
            ],
            order="id desc",
        )
        return res | product_template_attachments

    _sql_constraints = [
        (
            "barcode_uniq",
            "unique(active,barcode)",
            "A barcode can only be assigned to one active product  !",
        ),
    ]

    @api.model
    def _sort_lines_by_product(self, lines):
        """
        Use this method to sort lines on product code.
        The line object must have a sequence field.
        """
        if not hasattr(lines.__class__, "sequence"):
            raise UserError(
                _(
                    "Programming Error detected in product.product, "
                    "_sort_lines_by_product"
                )
            )
        lines = lines.sorted(lambda r: r.product_id.default_code or "")
        sequence = 0
        for line in lines:
            sequence += 1
            line.sequence = sequence



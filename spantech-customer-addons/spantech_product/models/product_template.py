# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    list_price = fields.Float(company_dependent=True)
    secondary_code = fields.Char(
        compute="_compute_secondary_code",
        inverse="_inverse_secondary_code",
        store=True,
    )
    project_type = fields.Selection(
        selection=[("S", "Sale"), ("R", "Rental"), ("I", "Internal")]
    )
    categ_id = fields.Many2one(default=False)
    invoice_policy = fields.Selection(company_dependent=True)
    produce_delay = fields.Float(company_dependent=True)
    days_to_prepare_mo = fields.Float(company_dependent=True)
    sale_delay = fields.Float(company_dependent=True)
    raw_material_id = fields.Many2one(comodel_name="product.template", string="Raw Material")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "company_id" in res:
            res.pop("company_id")
        return res

    @api.depends("product_variant_ids", "product_variant_ids.secondary_code")
    def _compute_secondary_code(self):
        unique_variants = self.filtered(
            lambda template: len(template.product_variant_ids) == 1
        )
        for template in unique_variants:
            template.secondary_code = template.product_variant_ids.secondary_code

        for template in self - unique_variants:
            template.secondary_code = False

    def _inverse_secondary_code(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.product_variant_ids.secondary_code = template.secondary_code

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
                ("res_id", "in", self.product_variant_ids.ids),
                ("res_model", "=", "product.product"),
            ],
            order="id desc",
        )
        return res | product_template_attachments

    @api.onchange("raw_material_id")
    def _onchange_raw_material_id(self):
        if self.raw_material_id:
            #self.standard_price = self.raw_material_id.standard_price * self.weight
            self.standard_price = 1000.0


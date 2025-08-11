from odoo import api, fields, models


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    x_pl_vat_gtu = fields.Many2one(comodel_name='jpk.gtu')

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id and self.product_id.product_tmpl_id.x_pl_vat_gtu:
            self.x_pl_vat_gtu = self.product_id.product_tmpl_id.x_pl_vat_gtu.id

    @api.model_create_multi
    def create(self, vals_list):
        # update GTU on lines
        for vals in vals_list:
            if vals.get('x_pl_vat_gtu'):
                continue

            if (
                self.env['account.move'].browse(vals['move_id']).is_sale_document()
                and vals.get('product_id')
                and not vals.get('exclude_from_invoice_tab')
            ):
                product_id = self.env['product.product'].browse([vals['product_id']])
                if product_id and product_id.x_pl_vat_gtu:
                    vals['x_pl_vat_gtu'] = product_id.x_pl_vat_gtu.id

        return super().create(vals_list)

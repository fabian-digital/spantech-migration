from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    x_enable_invoice_rate_change = fields.Boolean(related='company_id.x_enable_invoice_rate_change', readonly=False)
    x_use_trilab_invoice = fields.Boolean(related='company_id.x_use_ti', readonly=False)
    x_show_price_before_discount = fields.Boolean(related='company_id.x_show_price_before_discount', readonly=False)
    x_hide_zero_price_aml = fields.Boolean(related='company_id.x_hide_zero_price_aml', readonly=False)

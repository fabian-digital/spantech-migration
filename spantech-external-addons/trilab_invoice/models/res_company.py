from odoo import fields, models


class Company(models.Model):
    _inherit = 'res.company'

    x_enable_invoice_rate_change = fields.Boolean(string='Enable Invoice Rate Change')
    x_use_ti = fields.Boolean(string='Use Trilab Invoice Module')
    x_show_price_before_discount = fields.Boolean(string='Show Price Before Discount on Invoices')
    x_hide_zero_price_aml = fields.Boolean(string='Hide Zero Price AML on Invoices')

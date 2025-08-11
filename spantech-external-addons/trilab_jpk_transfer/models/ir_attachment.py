from odoo import fields, models


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    x_jpk_hash = fields.Char(string='JPK Hash')

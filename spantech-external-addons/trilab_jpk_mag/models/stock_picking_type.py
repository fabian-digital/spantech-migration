from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    x_jpk_mag = fields.Selection(
        selection=[
            ('JPK_PZ', 'JPK_PZ'), ('JPK_WZ', 'JPK_WZ'), ('JPK_RW', 'JPK_RW'), ('JPK_MM', 'JPK_MM')
        ],
        string='JPK MAG'
    )

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    default_show_qty_in_percentage = fields.Boolean(
        string="Show Quantity in percentage in the invoice (Default)",
    )

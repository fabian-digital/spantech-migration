from odoo import models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def x_jpk_get_summary_print_report_name(self):
        return self.name

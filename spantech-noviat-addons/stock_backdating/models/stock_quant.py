# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.tools import groupby


class StockQuant(models.Model):
    _inherit = "stock.quant"

    force_date = fields.Date()

    @api.model
    def _get_inventory_fields_write(self):
        """Returns a list of fields user can edit when editing a quant in `inventory_mode`."""
        res = super()._get_inventory_fields_write()
        res += ["force_date"]
        return res

    def _apply_inventory(self):
        for force_date, inventory_ids in groupby(self, key=lambda q: q.force_date):
            inventories = self.env["stock.quant"].concat(*inventory_ids)
            if force_date:
                super(
                    StockQuant, inventories.with_context(force_date=force_date)
                )._apply_inventory()
                inventories.force_date = False
            else:
                super(StockQuant, inventories)._apply_inventory()
        return

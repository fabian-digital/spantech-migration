# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    maintenance_information = fields.Text(string="Information")
    maintenance_equipment_id = fields.Many2one(
        comodel_name="maintenance.equipment",
        string="Equipment",
        help="The equipment being send for repair in this purchase order",
    )

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class Picking(models.Model):
    _inherit = "stock.picking"

    external_note = fields.Text()
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        store=True,
    )

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        Analytic = self.env["account.analytic.account"]
        for stock in self:
            if stock.analytic_distribution:
                acc_ids = Analytic.browse([int(k) for k in stock.analytic_distribution])
                stock.analytic_account_ids = acc_ids
            else:
                stock.analytic_account_ids = False

    def button_validate(self):
        res = super().button_validate()
        if self.env.context.get("copy_scheduled_date"):
            for rec in self:
                rec.date_done = rec.scheduled_date
        return res

    def action_type_code_set_all(self):
        for rec in self:
            try:
                for line in rec.move_ids_without_package:
                    if line.state not in ["done", "cancel"]:
                        if rec.picking_type_code == "incoming":
                            line.quantity_done = line.product_uom_qty
                        elif rec.picking_type_code == "internal":
                            line.quantity_done = line.reserved_availability
                        elif rec.picking_type_code == "outgoing":
                            line.quantity_done = line.reserved_availability
            except Exception:
                for line in rec.move_line_ids_without_package:
                    if line.state not in ["done", "cancel"]:
                        if rec.picking_type_code == "incoming":
                            line.qty_done = line.move_id.product_uom_qty
                        elif rec.picking_type_code == "internal":
                            line.qty_done = line.move_id.reserved_availability
                        elif rec.picking_type_code == "outgoing":
                            line.qty_done = line.move_id.reserved_availability

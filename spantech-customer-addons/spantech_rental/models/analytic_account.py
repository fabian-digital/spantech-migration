# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    sale_rental_ids = fields.One2many(
        inverse_name="analytic_account_id",
        comodel_name="sale.rental",
        string="Sale Rentals",
    )
    sale_rental_ids_count = fields.Integer(
        compute="_compute_sale_rental_ids_count",
    )

    @api.depends("sale_order_ids")
    def _compute_sale_rental_ids_count(self):
        for analytic_account in self:
            if analytic_account.sale_rental_ids:
                analytic_account.sale_rental_ids_count = len(
                    analytic_account.sale_rental_ids
                )
            else:
                analytic_account.sale_rental_ids_count = 0

    @api.depends("sale_order_ids.analytic_account_id")
    def _compute_sale_order_line_ids(self):
        for analytic_account in self:
            if analytic_account.sale_order_ids:
                sale_lines = analytic_account.sale_order_ids.order_line
                analytic_account.sale_order_line_ids = sale_lines
            else:
                analytic_account.sale_order_line_ids = False

    def action_open_sale_rentals(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "sale_rental.sale_rental_action"
        )
        action.update(
            {"domain": [("id", "in", self.sale_rental_ids.ids)], "context": {}}
        )
        return action

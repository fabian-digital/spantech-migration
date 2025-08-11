# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    rental_ids = fields.One2many(
        comodel_name="sale.rental", inverse_name="start_order_line_id"
    )
    rental_id = fields.Many2one(
        comodel_name="sale.rental", compute="_compute_rental_id", store=True
    )

    @api.constrains(
        "rental_type",
        "extension_rental_id",
        "start_date",
        "end_date",
        "rental_qty",
        "product_uom_qty",
        "product_id",
    )
    def _check_sale_line_rental(self):
        for line in self:
            if line.rental_type == "rental_extension":
                if not line.extension_rental_id:
                    raise ValidationError(
                        _(
                            "Missing 'Rental to Extend' on the sale order line "
                            "with rental service %s"
                        )
                        % line.product_id.display_name
                    )

                if line.rental_qty != line.extension_rental_id.rental_qty:
                    raise ValidationError(
                        _(
                            "On the sale order line with rental service {name}, "
                            "you are trying to extend a rental with a rental quantity"
                            " ({rent_qty}) that is different from the quantity of the"
                            " original rental ({ext_qty}). This is not supported."
                        ).format(
                            name=line.product_id.display_name,
                            rent_qty=line.rental_qty,
                            ext_qty=line.extension_rental_id.rental_qty,
                        )
                    )
            if line.rental_type in ("new_rental", "rental_extension"):
                if not line.product_id.rented_product_id:
                    raise ValidationError(
                        _(
                            "On the 'new rental' sale order line with product "
                            "'%s', we should have a rental service product !"
                        )
                        % line.product_id.display_name
                    )
                # the module sale_start_end_dates checks that, when we have
                # must_have_dates, we have start + end dates
            elif line.sell_rental_id:
                if line.product_uom_qty != line.sell_rental_id.rental_qty:
                    raise ValidationError(
                        _(
                            "On the sale order line with product %(name)s "
                            "you are trying to sell a rented product with a "
                            "quantity (%(prod_qty)s) that is different from the rented "
                            "quantity (%(rental_qty)s). This is not supported."
                        )
                        % {
                            "name": line.product_id.display_name,
                            "prod_qty": line.product_uom_qty,
                            "rental_qty": line.sell_rental_id.rental_qty,
                        }
                    )

    @api.depends("rental_ids")
    def _compute_rental_id(self):
        for line in self:
            if line.rental_ids:
                line.rental_id = line.rental_ids[0].id
            else:
                line.rental_id = False

    def _prepare_new_rental_procurement_values(self, group=False):
        vals = super()._prepare_new_rental_procurement_values(group)
        if self.order_id.analytic_account_id:
            vals["analytic_account_id"] = self.order_id.analytic_account_id
        return vals

    def _prepare_procurement_values(self, group_id=False):
        vals = super()._prepare_procurement_values(group_id)
        if self.order_id.analytic_account_id:
            vals["analytic_account_id"] = self.order_id.analytic_account_id
        return vals

    def action_launch_stock_rule(self):
        self.ensure_one()
        self._action_launch_stock_rule(previous_product_uom_qty={self.id: 0})

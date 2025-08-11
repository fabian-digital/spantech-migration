# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import _, api, fields, models
from odoo.exceptions import UserError

READONLY_STATES = {
    "purchase": [("readonly", False)],
    "done": [("readonly", False)],
    "cancel": [("readonly", False)],
}


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    picking_type_id = fields.Many2one(domain="[('company_id','=',company_id)]")
    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Company"
    )
    show_category_warning = fields.Boolean(
        compute="_compute_show_category_warning", store=True
    )
    order_type = fields.Many2one(
        states=READONLY_STATES,
    )
    analytic_account_ids = fields.Many2many(
        comodel_name="account.analytic.account",
        compute="_compute_analytic_account_ids",
        store=True,
    )
    analytic_distribution_blocking = fields.Char(
        compute="_compute_analytic_distribution_blocking"
    )

    qty_received_ratio_total = fields.Float(
        string="Received Quantity %",
    )

    qty_invoiced_ratio_total = fields.Float(
        string="Invoiced Quantity %",
    )

    amount_invoiced_ratio_total = fields.Float(
        string="Invoiced Amount %",
    )

    @api.depends("order_line.product_id", "order_line.product_id.categ_id")
    def _compute_show_category_warning(self):
        for purchase in self:
            if any(
                line.product_id.categ_id == self.env.ref("product.product_category_all")
                for line in purchase.order_line.filtered(lambda ol: not ol.display_type)
            ):
                purchase.show_category_warning = True
            else:
                purchase.show_category_warning = False

    @api.depends("analytic_distribution")
    def _compute_analytic_account_ids(self):
        for po in self:
            if po.analytic_distribution:
                acc_ids = self.env["account.analytic.account"].browse(
                    [int(k) for k in po.analytic_distribution]
                )
                po.analytic_account_ids = acc_ids
            else:
                po.analytic_account_ids = False

    def _compute_date_planned(self):
        for order in self:
            if not order.date_planned:
                super()._compute_date_planned()
        return

    @api.depends(
        "invoice_status",
        "order_line",
        "order_line.qty_invoiced",
        "force_invoiced",
    )
    def _compute_qty_invoiced_ratio_total(self):
        for purchase in self.filtered(lambda po: po.force_invoiced):
            purchase.qty_invoiced_ratio_total = 100
        super(
            PurchaseOrder, self.filtered(lambda po: not po.force_invoiced)
        )._compute_qty_invoiced_ratio_total()
        return

    @api.depends(
        "analytic_distribution", "order_line", "order_line.analytic_distribution"
    )
    def _compute_analytic_distribution_blocking(self):
        for order in self:
            blocking_account = []
            if order.analytic_distribution:
                for distribution in self.analytic_distribution:
                    account = self.env["account.analytic.account"].browse(
                        int(distribution)
                    )
                    if account.block_purchase:
                        blocking_account.append(account.name)
            for line in order.order_line:
                if line.analytic_distribution:
                    for distribution in line.analytic_distribution:
                        account = self.env["account.analytic.account"].browse(
                            int(distribution)
                        )
                        if account.block_purchase:
                            blocking_account.append(account.name)
            if blocking_account:
                order.analytic_distribution_blocking = _(
                    "No Purchase Orders can be confirmed for the following "
                    "project(s):\n\t%s\n Please contact the Finance Manager",
                    "\n\t".join(set(blocking_account)),
                )
            else:
                order.analytic_distribution_blocking = ""

    @api.onchange("commercial_partner_id")
    def onchange_partner_id(self):
        res = super().onchange_partner_id()
        if self.order_type:
            self.order_type = False
        if not self.commercial_partner_id:
            self.update(
                {
                    "partner_id": False,
                    "fiscal_position_id": False,
                }
            )
            return
        cp = self.commercial_partner_id
        addr = cp.address_get(["contact", "delivery", "invoice"])
        values = {
            "payment_term_id": cp.property_supplier_payment_term_id
            and cp.property_supplier_payment_term_id.id
            or False,
            "partner_id": addr["contact"],
        }
        self.update(values)
        return res

    def button_confirm(self):
        for order in self:
            if order.show_category_warning:
                raise UserError(
                    _(
                        "One of the products has the default category and it's not "
                        "allowed."
                    )
                )
            if order.analytic_distribution_blocking:
                raise UserError(order.analytic_distribution_blocking)
            if not order.user_id and self.env.user:
                order.user_id = self.env.user
        return super().button_confirm()

    def button_draft(self):
        if self.partner_id.is_interco_partner and not self.env.context.get(
            "from_wizard", False
        ):
            warning_wiz = self.env["change.state.warning.wizard"].create(
                {"purchase_order_id": self.id}
            )
            return {
                "type": "ir.actions.act_window",
                "name": _("Warning"),
                "view_mode": "form",
                "res_model": "change.state.warning.wizard",
                "target": "new",
                "res_id": warning_wiz.id,
            }
        return super().button_draft()

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        self.ensure_one()
        values = super()._prepare_sale_order_data(
            name, partner, company, direct_delivery_address
        )
        if self.analytic_account_ids:
            values["analytic_account_id"] = self.analytic_account_ids[0].id
        if partner:
            values["commercial_partner_id"] = partner.id
        return values

    def _prepare_invoice(self):
        invoice_vals = super()._prepare_invoice()
        if self.analytic_distribution:
            invoice_vals["analytic_distribution"] = self.analytic_distribution
        return invoice_vals

    def action_boom_kit(self):
        self.ensure_one()
        for line in self.order_line:
            bom_obj = self.env["mrp.bom"]
            if line.state in ["draft", "sent"] and line.product_id:
                boms_per_product = bom_obj._bom_find(
                    line.product_id,
                    company_id=line.company_id.id,
                    bom_type="phantom",
                )
                if boms_per_product:
                    for bom in boms_per_product.values():
                        for bom_line in bom.bom_line_ids:
                            line.create_line_from_kit_line(line.product_qty, bom_line)
                        line.unlink()

    def _get_under_validation_exceptions(self):
        res = super()._get_under_validation_exceptions()
        res += [
            "user_id",
        ]
        return res


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    def action_product_forecast_report(self):
        action = super().action_product_forecast_report()
        if self.order_id.analytic_account_ids:
            action["context"][
                "purchase_analytic_account"
            ] = self.order_id.analytic_account_ids[0].id
        return action

    def create_line_from_kit_line(self, parent_qty, bom_line):
        bom_obj = self.env["mrp.bom"]
        boms_per_product = bom_obj._bom_find(
            bom_line.product_id,
            company_id=self.company_id.id,
            bom_type="phantom",
        )
        if boms_per_product:
            for bom in boms_per_product.values():
                for sub_bom_line in bom.bom_line_ids:
                    self.create_line_from_kit_line(
                        parent_qty * bom_line.product_qty, sub_bom_line
                    )
        else:
            self.create(
                {
                    "name": bom_line.product_id.display_name,
                    "product_qty": parent_qty * bom_line.product_qty,
                    "order_id": self.order_id.id,
                    "price_unit": bom_line.product_id.standard_price,
                    "product_id": bom_line.product_id.id,
                    "analytic_distribution": self.analytic_distribution,
                    "date_planned": self.date_planned,
                    "product_uom": self.product_uom.id,
                }
            )

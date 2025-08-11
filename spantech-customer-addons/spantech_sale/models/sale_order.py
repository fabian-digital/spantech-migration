# Copyright 2009-2025 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError
from odoo.http import request


class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        compute="_compute_partner_id",
        store=True,
        readonly=False,
        required=True,
        precompute=True,
    )

    commitment_date = fields.Datetime(tracking=True)

    manual_invoice_ids = fields.Many2many("account.move", string="Manual Invoices")
    project_type = fields.Selection(related="analytic_account_id.project_type")
    show_category_warning = fields.Boolean(
        compute="_compute_show_category_warning", store=True
    )
    show_commitment_date_in_document = fields.Boolean(
        string="Show Commitment Date in Document", default=False
    )

    commercial_partner_id = fields.Many2one(
        comodel_name="res.partner", string="Company"
    )
    partner_verified_date = fields.Date(
        string="Verified Date", related="partner_id.verified_date"
    )
    analytic_account_domain = fields.Binary(
        compute="_compute_analytic_account_domain",
    )

    qty_delivered_ratio_total = fields.Float(
        string="Received Quantity %",
    )

    qty_invoiced_ratio_total = fields.Float(
        string="Invoiced Quantity %",
    )

    amount_invoiced_ratio_total = fields.Float(
        string="Invoiced Amount %",
    )

    last_delivery_date = fields.Date(compute="_compute_last_delivery_date", store=True)

    @api.onchange("commitment_date")
    def _onchange_commitment_date(self):
        """Update empty commitment date order lines with commitment date
        from sale order"""
        result = super()._onchange_commitment_date() or {}
        order_line_vals = []
        for order_line in self.order_line:
            order_line_vals.append(
                Command.update(order_line.id, {"commitment_date": self.commitment_date})
            )
        self.order_line = order_line_vals
        return result

    @api.depends("order_line.invoice_lines", "manual_invoice_ids")
    def _get_invoiced(self):
        super()._get_invoiced()
        for order in self:
            invoices = order.invoice_ids + order.manual_invoice_ids
            order.invoice_ids |= invoices
            order.invoice_count = len(invoices)
        return

    @api.depends("order_line.product_id", "order_line.product_id.categ_id")
    def _compute_show_category_warning(self):
        for sale in self:
            if any(
                line.product_id.categ_id == self.env.ref("product.product_category_all")
                for line in sale.order_line.filtered(lambda ol: not ol.display_type)
            ):
                sale.show_category_warning = True
            else:
                sale.show_category_warning = False

    @api.depends("picking_ids.date_done")
    def _compute_last_delivery_date(self):
        for order in self:
            pickings = order.picking_ids.filtered(
                lambda x: x.state == "done" and x.location_dest_id.usage == "customer"
            )
            dates_list = [date for date in pickings.mapped("date_done") if date]
            order.last_delivery_date = max(dates_list, default=False)

    @api.depends(
        "order_line",
        "order_line.qty_invoiced",
        "order_line.invoice_status",
        "force_invoiced",
    )
    def _compute_qty_invoiced_ratio_total(self):
        for sale in self.filtered(lambda s: s.force_invoiced):
            sale.qty_invoiced_ratio_total = 100
        super(
            SaleOrder, self.filtered(lambda so: not so.force_invoiced)
        )._compute_qty_invoiced_ratio_total()
        for sale in self.filtered(lambda so: not so.force_invoiced):
            super(SaleOrder, sale)._compute_qty_invoiced_ratio_total()
        return

    @api.depends("commercial_partner_id")
    def _compute_pricelist_id(self):
        super()._compute_pricelist_id()
        for order in self:
            if not order.commercial_partner_id:
                order.pricelist_id = False
                continue
            order = order.with_company(order.company_id)
            order.pricelist_id = order.commercial_partner_id.property_product_pricelist
        return

    @api.depends("commercial_partner_id")
    def _compute_payment_term_id(self):
        super()._compute_payment_term_id()
        for order in self:
            if not order.commercial_partner_id:
                order.payment_term_id = False
                continue
            order = order.with_company(order.company_id)
            order.payment_term_id = order.commercial_partner_id.property_payment_term_id
        return

    @api.depends("commercial_partner_id")
    def _compute_partner_id(self):
        for order in self:
            order.partner_id = (
                order.commercial_partner_id.address_get(["contact"])["contact"]
                if order.commercial_partner_id
                else False
            )

    @api.depends("commercial_partner_id")
    def _compute_partner_invoice_id(self):
        super()._compute_partner_invoice_id()
        for order in self:
            order.partner_invoice_id = (
                order.commercial_partner_id.address_get(["invoice"])["invoice"]
                if order.commercial_partner_id
                else False
            )
        return

    @api.depends("commercial_partner_id")
    def _compute_partner_shipping_id(self):
        super()._compute_partner_shipping_id()
        for order in self:
            order.partner_shipping_id = (
                order.commercial_partner_id.address_get(["delivery"])["delivery"]
                if order.commercial_partner_id
                else False
            )
        return

    @api.depends("commercial_partner_id")
    def _compute_analytic_account_domain(self):
        for sale in self:
            if sale.commercial_partner_id:
                company = self.env["res.company"]._find_company_from_partner(
                    sale.commercial_partner_id.id
                )
                if company:
                    sale.analytic_account_domain = []
                    continue
            sale.analytic_account_domain = [
                "|",
                ("partner_id", "=", sale.commercial_partner_id.id),
                ("partner_id", "=", False),
            ]

    def action_confirm(self):
        if self.show_category_warning:
            raise UserError(
                _("One of the products has the default category and it's not allowed.")
            )
        if (
            self.company_id.dummy_project_maximum_amount
            and self.amount_untaxed > self.company_id.dummy_project_maximum_amount
            and self.analytic_account_id.apply_threshold
        ):
            raise UserError(
                _("Your Sale Quotation Amount is too high " "to have a dummy project !")
            )
        if not self.partner_id.verified:
            raise UserError(
                _(
                    "Your Partner has to be verified if you want "
                    "to confim the sale quotation !"
                )
            )
        if self.project_type and self.order_line.filtered(
            lambda ol: ol.product_id.project_type
            and ol.product_id.project_type != self.project_type
        ):
            raise UserError(
                _(
                    "One of the lines used a product with a "
                    "project type different from the one "
                    "defined on the analytical account"
                )
            )
        return super().action_confirm()

    def download_plans(self):
        prod_attach = self.env["ir.attachment"]
        for pl in self.order_line:
            if pl.product_id:
                domain = [
                    ("name", "=like", f"{pl.product_id.default_code[:7]}%"),
                    "|",
                    "&",
                    ("res_model", "=", "product.product"),
                    ("res_id", "=", pl.product_id.id),
                    "&",
                    ("res_model", "=", "product.template"),
                    ("res_id", "=", pl.product_id.product_tmpl_id.id),
                ]
                prod_attach += self.env["ir.attachment"].search(domain)
        if len(prod_attach) > 0:
            ids = ",".join(map(str, prod_attach.ids))
            url = f"{request.httprequest.host_url}web/attachment/download_zip?ids={ids}"
            return {
                "type": "ir.actions.act_url",
                "url": url,
                "target": "self",
            }

    def _prepare_invoice(self):
        res = super()._prepare_invoice()
        if self.analytic_account_id:
            res["analytic_distribution"] = {self.analytic_account_id.id: 100}
        if self.partner_id.property_out_journal_id:
            res["journal_id"] = self.partner_id.property_out_journal_id.id
        res["narration"] = self.company_id.with_context(
            lang=self.partner_id.lang or self.env.lang
        ).invoice_terms
        return res

    def _prepare_purchase_order_data(self, company, company_partner):
        values = super()._prepare_purchase_order_data(company, company_partner)
        if self.analytic_account_id:
            values["analytic_distribution"] = {self.analytic_account_id.id: 100}
        return values

    @api.model
    def _prepare_purchase_order_line_data(self, so_line, date_order, company):
        values = super()._prepare_purchase_order_line_data(so_line, date_order, company)
        if so_line.order_id.analytic_account_id:
            values["analytic_distribution"] = {
                so_line.order_id.analytic_account_id.id: 100
            }
        return values

    def sort_by_product(self):
        self.env["product.product"]._sort_lines_by_product(self.order_line)
        return True


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    total_weight = fields.Float(compute="_compute_total_weight", store=True)

    @api.onchange("product_id")
    def _onchange_product_id_warning(self):
        res = super()._onchange_product_id_warning()
        if (
            self.product_id
            and self.product_id.project_type
            and self.order_id.project_type
            and self.order_id.project_type != self.product_id.project_type
        ):
            raise UserError(
                _(
                    "The project type of the product is "
                    "different from the one defined on the analytical account"
                )
            )
        return res

    @api.depends("product_uom_qty")
    def _compute_total_weight(self):
        for rec in self:
            rec.total_weight = rec.product_uom_qty * rec.product_id.weight

    @api.depends()
    def _compute_qty_to_invoice(self):
        for line in self:
            line = line.with_company(line.order_id.company_id)
            super(SaleOrderLine, line)._compute_qty_to_invoice()
        return

    def _prepare_invoice_line(self, **optional_values):
        line_vals = super()._prepare_invoice_line(**optional_values)
        if self.env.context.get("partial_invoice_percent", False):
            line_vals["quantity"] = min(
                line_vals["quantity"],
                self.product_qty * self.env.context["partial_invoice_percent"],
            )
        return line_vals

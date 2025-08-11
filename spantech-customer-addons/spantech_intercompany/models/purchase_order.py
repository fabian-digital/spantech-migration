# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    spantech_automatic_intercompany_document = fields.Boolean(
        string="Intercompany - Automatic Generation",
        help="In the case another Spantech Entity is the partner, "
        "ticking this box will (if activated) generate "
        "the inverse document in the other entity.",
        copy=False,
        compute="_compute_spantech_automatic_intercompany_document",
        store=True,
    )

    is_interco_partner = fields.Boolean(
        related="partner_id.is_interco_partner",
        store=True,
        string="Is a Spantech Entity",
    )

    intercompany_sale_order_ids = fields.One2many(
        comodel_name="sale.order", inverse_name="auto_purchase_order_id"
    )

    intercompany_commitment_date = fields.Datetime(
        string="Date Confirmed",
        compute="_compute_intercompany_commitment_date",
        store=True,
        tracking=True,
    )

    @api.depends(
        "intercompany_sale_order_ids", "intercompany_sale_order_ids.commitment_date"
    )
    def _compute_intercompany_commitment_date(self):
        for rec in self:
            sale_orders = rec.intercompany_sale_order_ids.filtered(
                lambda o: o.state != "cancel"
            )
            if sale_orders and sale_orders[0].commitment_date:
                rec.intercompany_commitment_date = sale_orders[0].commitment_date
            else:
                rec.intercompany_commitment_date = False

    @api.depends("is_interco_partner")
    def _compute_spantech_automatic_intercompany_document(self):
        for order in self:
            order.spantech_automatic_intercompany_document = order.is_interco_partner

    @api.model_create_multi
    def create(self, vals_list):
        purchases = super().create(vals_list)
        for purchase in purchases:
            if purchase.auto_generated and purchase.auto_sale_order_id:
                if purchase.company_id.interco_po_notif_user_ids:
                    user_to_notify = purchase.company_id.interco_po_notif_user_ids
                    purchase.message_post(
                        body=_(
                            "Sale Order %(sale_name)s (from Spantech Entity: "
                            "%(company_name)s) created this purchase order"
                        ).format(
                            sale_name=purchase.auto_sale_order_id.name,
                            company_name=purchase.auto_sale_order_id.company_id.code,
                        ),
                        partner_ids=user_to_notify.partner_id.ids,
                        subtype_id=self.env.ref("mail.mt_note").id,
                        email_layout_xmlid="mail.mail_notification_light",
                    )
        return purchases

    def _compute_date_planned(self):
        return super(
            PurchaseOrder, self.filtered(lambda o: not o.is_interco_partner)
        )._compute_date_planned()

    def button_confirm(self):
        for purchase in self:
            if purchase.is_interco_partner and not purchase.date_planned:
                raise UserError(
                    _("You must set the Expected Arrival for inter-company purchase.")
                )
        return super().button_confirm()

    def button_cancel(self):
        if self.is_interco_partner:
            sale_id = (
                self.env["sale.order"].sudo().search([("name", "=", self.partner_ref)])
            )
            if sale_id:
                sale_id.message_post(
                    body=_("Purchase Order %(po_link)s has been cancelled.")
                    % {
                        "po_link": self._get_html_link(),
                    }
                )
                template_id = self.env.ref("spantech_intercompany.mail_cancel_po")
                template_id.send_mail(self.id)
        return super().button_cancel()

    def inter_company_create_sale_order(self, company):
        allowed_purchases = self.filtered(
            lambda po: po.spantech_automatic_intercompany_document
        )
        if allowed_purchases:
            return super(
                PurchaseOrder, allowed_purchases
            ).inter_company_create_sale_order(company)
        else:
            return False

    def _prepare_sale_order_data(self, name, partner, company, direct_delivery_address):
        values = super()._prepare_sale_order_data(
            name, partner, company, direct_delivery_address
        )
        if values.get("commitment_date", False):
            values.pop("commitment_date")
        if "origin" not in values and self.origin:
            values["origin"] = self.origin
        values["date_order"] = self.date_approve
        values["expected_date"] = self.date_planned
        values["note"] = self.notes
        return values

    @api.model
    def _prepare_sale_order_line_data(self, line, company):
        vals = super()._prepare_sale_order_line_data(line, company)
        vals["commitment_date"] = line.date_planned
        vals["auto_generated"] = True
        vals["auto_purchase_order_line_id"] = line.id
        return vals


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    auto_generated = fields.Boolean(string="Auto Generated Purchase Order", copy=False)
    auto_sale_order_line_id = fields.Many2one(
        "sale.order.line", string="Source Sales Order Line", readonly=True, copy=False
    )
    date_planned = fields.Datetime()
    sale_effective_date = fields.Datetime(tracking=True, string="Date Confirmed")

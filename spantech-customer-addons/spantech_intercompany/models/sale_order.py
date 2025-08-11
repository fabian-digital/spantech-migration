# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

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

    intercompany_buyer = fields.Char(
        string="ICO Buyer",
        help="Inter company Buyer",
        compute="_compute_intercompany_buyer",
        compute_sudo=True,
    )

    intercompany_date_planned = fields.Datetime(
        string="ICO Expected", related="auto_purchase_order_id.date_planned"
    )

    def _compute_intercompany_buyer(self):
        for order in self:
            if order.auto_purchase_order_id:
                order.intercompany_buyer = (
                    order.auto_purchase_order_id.user_id.display_name
                )
            else:
                order.intercompany_buyer = ""

    @api.depends("is_interco_partner")
    def _compute_spantech_automatic_intercompany_document(self):
        for order in self:
            order.spantech_automatic_intercompany_document = order.is_interco_partner

    @api.onchange("partner_id")
    def _onchange_show_commitment_date_in_document(self):
        show_commitment_date = False
        if self.partner_id and self.is_interco_partner:
            show_commitment_date = True
        self.show_commitment_date_in_document = show_commitment_date

    @api.model_create_multi
    def create(self, vals_list):
        sales = super().create(vals_list)
        for sale in sales:
            if sale.auto_generated and sale.auto_purchase_order_id:
                if sale.company_id.interco_so_notif_user_ids:
                    user_to_notify = sale.company_id.interco_so_notif_user_ids
                    sale.message_post(
                        body=_(
                            "Purchase Order %(purchase_name)s "
                            "(from Spantech Entity: %(company_name)s) "
                            "created this sale order"
                        )
                        % {
                            "purchase_name": sale.auto_purchase_order_id.name,
                            "company_name": sale.auto_purchase_order_id.company_id.code,
                        },
                        partner_ids=user_to_notify.partner_id.ids,
                        subtype_id=self.env.ref("mail.mt_note").id,
                        email_layout_xmlid="mail.mail_notification_light",
                    )
        return sales

    def inter_company_create_purchase_order(self, company):
        allowed_sales = self.filtered(
            lambda so: so.spantech_automatic_intercompany_document
        )
        if allowed_sales:
            return super(SaleOrder, allowed_sales).inter_company_create_purchase_order(
                company
            )
        else:
            return False

    def action_confirm(self):
        res = super().action_confirm()
        for line in self.order_line.filtered(lambda x: x.auto_generated):
            line.auto_purchase_order_line_id.sudo().sale_effective_date = (
                line.commitment_date
            )
        return res

    def write(self, values):
        for sale in self:
            if sale.auto_generated and values.get("note", False):
                if sale.auto_purchase_order_id:
                    apo = sale.auto_purchase_order_id
                    apo.sudo().notes = values.get("note")
            if (
                "commitment_date" in values
                and sale.commitment_date != values.get("commitment_date")
                and sale.auto_purchase_order_id
            ):
                sale.with_context(
                    force_notify_email=True
                ).auto_purchase_order_id.sudo().message_post(
                    body=_(
                        "Sale Order %(sale_name)s "
                        "(from Spantech Entity: %(company_name)s)<br/>"
                        "<li> Delivery date change :  %(old_commitment_date)s "
                        "-> %(new_commitment_date)s</li>"
                    )
                    % {
                        "sale_name": sale.name,
                        "company_name": sale.company_id.code,
                        "old_commitment_date": sale.commitment_date,
                        "new_commitment_date": values["commitment_date"],
                    },
                    partner_ids=sale.sudo().auto_purchase_order_id.user_id.partner_id.ids,
                    subtype_id=self.env.ref("mail.mt_note").id,
                    email_layout_xmlid="mail.mail_notification_light",
                )
        return super().write(values)


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    auto_generated = fields.Boolean(string="Auto Generated Sales Order", copy=False)
    auto_purchase_order_line_id = fields.Many2one(
        "purchase.order.line",
        string="Source Purchase Order Line",
        readonly=True,
        copy=False,
    )

    def write(self, values):
        for sale_order_line in self:
            if (
                sale_order_line.auto_generated
                and sale_order_line.auto_purchase_order_line_id
                and (
                    values.get("commitment_date", False)
                    or values.get("price_unit", False)
                )
            ):
                apol = sale_order_line.auto_purchase_order_line_id
                if values.get("commitment_date"):
                    apol.sudo().sale_effective_date = values.get("commitment_date")
                if values.get("price_unit"):
                    old_price = sale_order_line.price_unit
                    apol.sudo().price_unit = values.get("price_unit")
                    apol.sudo().order_id.message_post(
                        body=(
                            _(
                                "Unit Price : %(purchase_name)s : "
                                "%(old_price)s --> %(new_price)s "
                            )
                            % {
                                "purchase_name": apol.sudo().display_name,
                                "old_price": old_price,
                                "new_price": values.get("price_unit"),
                            }
                        )
                    )
        return super().write(values)

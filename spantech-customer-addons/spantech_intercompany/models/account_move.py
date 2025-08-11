# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    generated_invoice_ids = fields.One2many(
        comodel_name="account.move", inverse_name="auto_invoice_id"
    )
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
    is_interco_commercial_partner = fields.Boolean(
        related="commercial_partner_id.is_interco_partner",
        store=True,
        string="Is a Spantech Entity (Commercial Partner)",
    )
    intercompany_lines = fields.Boolean(
        compute="_compute_intercompany_lines",
        store=True,
        string="Intercompany Invoice (All lines)",
    )
    show_intercompany_warning = fields.Boolean(
        compute="_compute_show_intercompany_warning",
        store=True,
    )
    can_generate_intercompany_move = fields.Boolean(
        compute="_compute_can_generate_intercompany_move",
    )

    @api.depends(
        "is_interco_partner",
        "line_ids.product_id",
        "line_ids.product_id.is_spantech_intercompany_product",
    )
    def _compute_intercompany_lines(self):
        for move in self:
            if all(
                line.product_id and line.product_id.is_spantech_intercompany_product
                for line in move.invoice_line_ids.filtered(
                    lambda aml: not aml.display_type
                )
            ):
                move.intercompany_lines = True
            else:
                move.intercompany_lines = False

    @api.depends("is_interco_commercial_partner", "is_interco_partner")
    def _compute_show_intercompany_warning(self):
        for move in self:
            if not move.is_interco_partner and move.is_interco_commercial_partner:
                move.show_intercompany_warning = True
            else:
                move.show_intercompany_warning = False

    @api.depends("is_interco_partner", "partner_id.intercompany_id")
    def _compute_can_generate_intercompany_move(self):
        for move in self:
            can_generate_intercompany_move = False
            if (
                move.partner_id.intercompany_id
                and move.partner_id.intercompany_id.rule_type
                and not move.auto_generated
                and move.spantech_automatic_intercompany_document
            ):
                if move.partner_id.intercompany_id.rule_type not in [
                    "invoice_and_refund",
                    "not_synchronize",
                ]:
                    can_generate_intercompany_move = True
            move.can_generate_intercompany_move = can_generate_intercompany_move

    @api.depends("is_interco_partner")
    def _compute_spantech_automatic_intercompany_document(self):
        for invoice in self:
            invoice.spantech_automatic_intercompany_document = (
                invoice.is_interco_partner
            )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.is_interco_partner and self.move_type in ("out_invoice", "out_refund"):
            self.show_analytic_in_document = True
        return res

    def action_post(self):
        for move in self:
            if move.show_intercompany_warning and (
                move.is_sale_document() or move.is_purchase_document()
            ):
                raise UserError(
                    _(
                        "In the case of Interco invoicing, you have to select "
                        "the entity itself and not a contact from the Spantech Entity."
                    )
                )
        return super().action_post()

    def _inter_company_prepare_invoice_data(self, invoice_type):
        self.ensure_one()
        values = super()._inter_company_prepare_invoice_data(invoice_type)
        if (
            invoice_type in ("in_invoice", "in_refund")
            and self.company_id.partner_id.property_in_journal_id
        ):
            values["journal_id"] = self.company_id.partner_id.property_in_journal_id.id
        elif (
            invoice_type in ("out_invoice", "out_refund")
            and self.company_id.partner_id.property_out_journal_id
        ):
            values["journal_id"] = self.company_id.partner_id.property_out_journal_id.id
        if self.analytic_distribution:
            values["analytic_distribution"] = self.analytic_distribution
        return values

    def _inter_company_create_invoices(self):
        allowed_moves = self.filtered(
            lambda m: m.spantech_automatic_intercompany_document
        )
        if not allowed_moves:
            return False
        moves = super(AccountMove, allowed_moves)._inter_company_create_invoices()
        for move in moves:
            move._onchange_partner_id()
            if move.auto_generated and move.auto_invoice_id:
                if (
                    not move.auto_invoice_id.intercompany_lines
                    and move.company_id.rule_type
                    not in ["invoice_and_refund", "not_synchronize"]
                ):
                    move.sudo().line_ids.unlink()
                if move.company_id.interco_am_notif_user_ids:
                    user_to_notify = move.company_id.interco_am_notif_user_ids
                    move.message_post(
                        body=_(
                            "Move %(move_name)s (from Spantech Entity: "
                            "%(company_name)s) created this account move"
                        ).format(
                            move_name=move.auto_invoice_id.name,
                            company_name=move.auto_invoice_id.company_id.code,
                        ),
                        partner_ids=user_to_notify.partner_id.ids,
                        subtype_id=self.env.ref("mail.mt_note").id,
                        email_layout_xmlid="mail.mail_notification_light",
                    )

    def _post(self, soft=True):
        invoices_map = {}
        posted = super()._post(soft)
        for invoice in posted.filtered(
            lambda move: move.is_invoice() and move.is_interco_partner
        ):
            if invoice.can_generate_intercompany_move:
                invoices_map.setdefault(
                    invoice.partner_id.intercompany_id, self.env["account.move"]
                )
                invoices_map[invoice.partner_id.intercompany_id] += invoice
        for company, invoices in invoices_map.items():
            invoices.with_user(company.intercompany_user_id).with_context(
                default_company_id=company.id, default_journal_id=None
            ).with_company(company)._inter_company_create_invoices()
        return posted


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    is_interco_partner = fields.Boolean(
        related="partner_id.is_interco_partner",
        store=True,
        string="Is a Spantech Entity",
    )

    def _inter_company_prepare_invoice_line_data(self):
        values = super()._inter_company_prepare_invoice_line_data()
        if self.product_id:
            if (
                self.purchase_line_id
                and self.purchase_line_id.order_id.auto_generated
                and self.purchase_line_id.order_id.auto_sale_order_id
            ):
                qty_to_invoice = self.quantity
                sale_line_ids = []
                sale_order = self.purchase_line_id.order_id.auto_sale_order_id
                for sale_line in sale_order.order_line.filtered(
                    lambda ol: ol.product_id == self.product_id
                    and ol.qty_to_invoice > 0
                ):
                    if qty_to_invoice > 0:
                        if qty_to_invoice <= sale_line.qty_to_invoice:
                            sale_line_ids.append((4, sale_line.id))
                            qty_to_invoice = 0
                        else:
                            sale_line_ids.append((4, sale_line.id))
                            qty_to_invoice -= sale_line.qty_to_invoice
                values["sale_line_ids"] = sale_line_ids
            elif self.sale_line_ids and self.sale_line_ids.mapped("order_id").filtered(
                lambda o: o.auto_generated
            ):
                qty_to_invoice = self.quantity
                purchase_line_id = self.env["purchase.order.line"]
                purchase_order = self.sale_line_ids.order_id.auto_purchase_order_id
                for purchase_line in purchase_order.order_line.filtered(
                    lambda pl: pl.product_id == self.product_id
                    and pl.qty_to_invoice > 0
                ):
                    if qty_to_invoice > 0 and not purchase_line_id:
                        if qty_to_invoice <= purchase_line.qty_to_invoice:
                            purchase_line_id = purchase_line
                            qty_to_invoice = 0
                        else:
                            purchase_line_id = purchase_line
                            qty_to_invoice -= purchase_line.qty_to_invoice
                values["purchase_line_id"] = purchase_line_id
        return values

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, models

_logger = logging.getLogger(__name__)


class Picking(models.Model):
    _inherit = "stock.picking"

    def button_validate(self):
        res = super().button_validate()
        for picking in self:
            if (
                picking.sale_id.auto_generated
                and picking.sale_id.auto_purchase_order_id
            ):
                picking._auto_validate_dropship_intercompany()
        return res

    def _auto_validate_dropship_intercompany(self):
        self.ensure_one()
        self = self.sudo()
        dropship_pickings = self.env["stock.picking"]
        for origin_picking in self.sale_id.auto_purchase_order_id.picking_ids.filtered(
            lambda p: p.state in ("assigned", "confirmed")
        ):
            if (
                origin_picking.location_dest_id.usage == "customer"
                and origin_picking.location_id.usage == "supplier"
            ):
                dropship_pickings |= origin_picking
        if dropship_pickings:
            for move in self.move_line_ids.filtered(lambda m: m.state == "done"):
                qty_to_assign = move.qty_done
                for dropship_move in dropship_pickings.mapped("move_line_ids").filtered(
                    lambda ml, m=move: ml.product_id == m.product_id
                    and ml.state not in ("done", "draft", "cancel")
                ):
                    if qty_to_assign > 0:
                        if qty_to_assign <= dropship_move.reserved_qty:
                            dropship_move.qty_done = qty_to_assign
                            qty_to_assign = 0
                        else:
                            dropship_move.qty_done = dropship_move.reserved_qty
                            qty_to_assign -= dropship_move.reserved_qty
            for dropship_picking in dropship_pickings:
                if any(
                    move_line.qty_done for move_line in dropship_picking.move_line_ids
                ):
                    dropship_picking.button_validate()
                    if dropship_picking.state == "done" and dropship_picking.sale_id:
                        dropship_picking.sale_id.message_post(
                            body=_(
                                "Picking %(origin_picking_name)s "
                                "(from Spantech Entity: %(company_name)s) "
                                "validated the dropshipment "
                                "<a href=# data-oe-model=stock.picking "
                                "data-oe-id=%(picking_id)d>%(picking_name)s</a>."
                            )
                            % {
                                "origin_picking_name": self.name,
                                "company_name": self.company_id.code,
                                "picking_id": dropship_picking.id,
                                "picking_name": dropship_picking.name,
                            },
                            partner_ids=dropship_picking.sale_id.user_id.partner_id.ids,
                            subtype_id=self.env.ref("mail.mt_note").id,
                            email_layout_xmlid="mail.mail_notification_light",
                        )

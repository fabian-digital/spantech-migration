# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    def register_as_main_attachment(self, force=True):
        res = super().register_as_main_attachment(force=force)
        if self.res_model == "account.move":
            related_record = (
                self.env[self.res_model].sudo().browse(self.res_id).exists()
            )
            if (
                related_record.state == "posted"
                and related_record.message_main_attachment_id
                and related_record.generated_invoice_ids
                and len(related_record.generated_invoice_ids) > 0
                and not related_record.generated_invoice_ids[
                    0
                ].message_main_attachment_id
            ):
                attachment = self.sudo().copy(
                    {
                        "company_id": related_record.generated_invoice_ids[
                            0
                        ].company_id.id,
                        "res_id": related_record.generated_invoice_ids[0].id,
                    }
                )
                related_record.generated_invoice_ids[0].write(
                    {"message_main_attachment_id": attachment.id}
                )
        return res

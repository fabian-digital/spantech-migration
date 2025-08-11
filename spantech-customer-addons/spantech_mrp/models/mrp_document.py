# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, models

_logger = logging.getLogger(__name__)


class MrpDocument(models.Model):
    _inherit = "mrp.document"

    @api.model
    def create(self, vals):
        res = super(MrpDocument, self.with_context(mrp_document=True)).create(vals)
        return res

    # code from Odoo V16
    def unlink(self):
        self.mapped("ir_attachment_id").unlink()
        return super().unlink()

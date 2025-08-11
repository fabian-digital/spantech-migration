# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class TierReview(models.Model):
    _inherit = "tier.review"

    def unlink(self):
        if self.env.context.get("disable_automatic_review_deletion"):
            return
        else:
            return super().unlink()

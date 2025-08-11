# Copyright 2009-2022 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models


class ValidationForwardWizard(models.TransientModel):
    _inherit = "tier.validation.forward.wizard"
    _description = "Forward Wizard"

    def add_forward(self):
        self.ensure_one()
        res = super().add_forward()
        rec = self.env[self.res_model].browse(self.res_id)
        if rec._name == "account.move" and self.forward_reviewer_id:
            rec.with_context(force_write_under_validation=True).write(
                {"approver_id": self.forward_reviewer_id.id}
            )
        return res

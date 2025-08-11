# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import fields, models


class TierValidation(models.AbstractModel):
    _inherit = "tier.validation"

    can_restart_validation = fields.Boolean(compute="_compute_can_restart_validation")

    def _compute_can_restart_validation(self):
        for validation in self:
            validation.can_restart_validation = True

    def write(self, vals):
        if (
            vals.get(self._state_field) in (self._state_from + [self._cancel_state])
            and vals.get(self._state_field) in self._state_to
        ):
            self = self.with_context(disable_automatic_review_deletion=True)
        return super().write(vals)

    def _check_allow_write_under_validation(self, vals):
        if self.env.context.get("force_write_under_validation"):
            return True
        else:
            return super()._check_allow_write_under_validation(vals)

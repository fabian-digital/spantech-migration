from odoo import api, fields, models


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    state_id = fields.Many2one(
        comodel_name="account.analytic.account.state",
        string="State",
        ondelete="restrict",
        tracking=True,
        index=True,
        copy=False,
        group_expand="_read_group_state_ids",
        default=lambda self: self._default_state_id(),
    )

    @api.model
    def _default_state_id(self):
        return (
            self.env["account.analytic.account.state"]
            .search([("fold", "=", False)], limit=1)
            .id
        )

    @api.model
    def _read_group_state_ids(self, stages, domain, order):
        return self.env["account.analytic.account.state"].search([], order=order)

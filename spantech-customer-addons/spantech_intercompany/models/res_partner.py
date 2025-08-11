# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = "res.partner"

    is_interco_partner = fields.Boolean(string="Is a Spantech Entity")
    intercompany_id = fields.Many2one(
        comodel_name="res.company",
        string="Intercompany",
        compute="_compute_intercompany_id",
        store=True,
    )

    @api.depends("is_interco_partner")
    def _compute_intercompany_id(self):
        for partner in self:
            if partner.is_interco_partner:
                company = self.env["res.company"]._find_company_from_partner(partner.id)
                if company:
                    partner.intercompany_id = company.id
                else:
                    partner.intercompany_id = False
            else:
                partner.intercompany_id = False

    def write(self, vals):
        if "is_interco_partner" in vals and self.env.user != self.env.ref(
            "base.user_admin"
        ):
            raise UserError(_("Only the administator can change this parameter"))
        return super().write(vals)

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    property_old_erp_customer_ref = fields.Char(
        string="Old ERP Customer Ref.", company_dependent=True
    )
    property_old_erp_supplier_ref = fields.Char(
        string="Old ERP Supplier Ref.", company_dependent=True
    )
    verified = fields.Boolean(tracking=True)
    verified_date = fields.Date(
        compute="_compute_verified_date",
        tracking=True,
        store=True,
    )

    email_hubspot = fields.Char(tracking=True)

    @api.depends("verified")
    def _compute_verified_date(self):
        for partner in self:
            if partner.verified:
                partner.verified_date = fields.Date.today()
            else:
                partner.verified_date = False

    @property
    def _order(self):
        res = super()._order
        partner_search_mode = self.env.context.get("res_partner_search_mode")
        verified_partner_search_mode = self.env.context.get(
            "verified_partner_search_mode"
        )
        if partner_search_mode not in ("customer", "supplier"):
            return res
        if not verified_partner_search_mode:
            return res
        order_by_field = "%s DESC"
        if partner_search_mode == "customer":
            field = "verified"
        else:
            return res

        order_by_field = order_by_field % field
        return f"{order_by_field}, {res}" if res else order_by_field

    def _get_name(self):
        name = super()._get_name()
        if "commit_assetsbundle" in self.env.context:
            return name
        partner = self
        if partner.verified:
            name = "[V] " + name
        return name

    @api.depends(
        "is_company",
        "name",
        "parent_id.display_name",
        "type",
        "company_name",
        "commercial_company_name",
        "verified",
    )
    def _compute_display_name(self):
        return super()._compute_display_name()

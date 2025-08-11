# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    interco_po_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="interco_po_notif_user_rel",
        string="Purchase Users to notify",
        help="When a purchase order is created via a Spantech entity, "
        "these users will be notified of the creation. ",
    )
    interco_so_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="interco_so_notif_user_rel",
        string="Sale Users to notify",
        help="When a sale order is created via a Spantech entity, "
        "these users will be notified of the creation. ",
    )
    interco_am_notif_user_ids = fields.Many2many(
        comodel_name="res.users",
        relation="interco_am_notif_user_rel",
        string="Accounting Users to notify",
        help="When a account move is created via a Spantech entity, "
        "these users will be notified of the creation. ",
    )
    purchase_intercompany_report_company_ids = fields.Many2many(
        comodel_name="res.company",
        relation="purchase_intercompany_report_company_ids_rel",
        column1="source_company_id",
        column2="report_company_id",
        string="Companies to show in Intercompany purchase report",
    )

    @api.model
    def create(self, vals):
        company = super().create(vals)
        if company and company.partner_id:
            company.partner_id.is_interco_partner = True
        return company

# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountAnalyticAccountDetail(models.Model):
    _name = "account.analytic.account.detail"
    _description = "Analytic Account Details"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account", string="Analytic Account"
    )
    country_id = fields.Many2one(comodel_name="res.country", string="Location")
    segment_id = fields.Many2one(comodel_name="res.partner.industry", string="Segment")
    dimension = fields.Char()
    name = fields.Char(string="Project Nickname")
    billing_entity_id = fields.Many2one(
        comodel_name="res.company", string="Billing Entity"
    )
    billing_entity_code = fields.Char(
        string="Entity Code", related="billing_entity_id.code"
    )
    billing_country_id = fields.Many2one(
        comodel_name="res.country",
        string="Billing Country",
        related="billing_entity_id.country_id",
        store=True,
    )
    project_total_amount = fields.Float(string="Total Amount of Project")
    date_sale = fields.Date(string="Sale Date")
    structure_type = fields.Char(string="Type of structure")


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    name = fields.Char(compute="_compute_name", store=True, required=False)
    code = fields.Char(string="Reference (Force project name)")
    approver_id = fields.Many2one(comodel_name="res.users", string="Approver")
    company_id = fields.Many2one(default=False)
    project_type = fields.Selection(
        selection=[("S", "Sale"), ("R", "Rental"), ("I", "Internal")]
    )
    customer_reference = fields.Char(size=4)
    seq_number = fields.Char(
        string="Sequential Number",
    )
    apply_threshold = fields.Boolean(string="Apply Threshold in sale")
    analytic_account_detail_ids = fields.One2many(
        comodel_name="account.analytic.account.detail",
        inverse_name="analytic_account_id",
        string="Analytic Details",
    )
    segment_id = fields.Many2one(
        comodel_name="res.partner.industry",
        string="Segment",
        compute="_compute_segment_id",
        store=True,
    )
    segment = fields.Char(related="segment_id.segment", store=True)
    subsegment = fields.Char(related="segment_id.subsegment", store=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.now())
            vals["seq_number"] = self.env["ir.sequence"].next_by_code(
                "account.analytic.account.seq", sequence_date=seq_date
            )
        return super().create(vals_list)

    def name_get(self):
        res = []
        super().name_get()
        for analytic in self:
            name = analytic.name
            res.append((analytic.id, name))
        return res

    @api.depends("code", "customer_reference", "project_type", "seq_number")
    def _compute_name(self):
        for analytic in self:
            if analytic.code:
                analytic.name = analytic.code
            else:
                name = fields.Date.to_string(
                    analytic.create_date or fields.Date.today()
                )[3]
                if analytic.seq_number:
                    name += analytic.seq_number
                else:
                    name += "000"
                if analytic.project_type:
                    name += analytic.project_type
                if analytic.customer_reference:
                    name += analytic.customer_reference
                analytic.name = name.upper()

    @api.depends("analytic_account_detail_ids.segment_id")
    def _compute_segment_id(self):
        for analytic in self:
            segment = self.env["res.partner.industry"]
            for detail in analytic.analytic_account_detail_ids:
                if not segment and detail.segment_id:
                    segment = detail.segment_id
            analytic.segment_id = segment

    _sql_constraints = [
        ("code", "unique(code)", "`code` must be unique."),
    ]

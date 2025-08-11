# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class HelpdekTicket(models.Model):
    _inherit = "helpdesk.ticket"

    analytic_account_id = fields.Many2one(
        comodel_name="account.analytic.account",
        string="Analytic Account",
        help="Select Project Code or “0000” if not project-related issue",
    )
    category_of_incident_id = fields.Many2one(
        comodel_name="helpdesk.ticket.category.incident"
    )
    reported_by_id = fields.Many2one(
        comodel_name="helpdesk.ticket.reporter",
        help="Who identified the incident (if known)",
    )
    is_show_customer_fields = fields.Boolean(
        related="ticket_type_id.is_show_customer_fields"
    )
    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")
    customer_name = fields.Char(
        compute="_compute_customer_name",
        store=True,
        readonly=False,
    )
    customer_email = fields.Char(
        compute="_compute_customer_email",
        store=True,
        readonly=False,
    )
    impact_of_incident = fields.Text()
    solution_to_incident = fields.Text()
    estimated_cost = fields.Float(
        digits="Product Price",
        help="Estimated cost (material + time) to solve the issue",
    )
    ticket_number = fields.Char(
        help="Will be defined automatically (unique reference among all companies)",
    )
    tag_ids = fields.Many2many(
        string="Impact",
        help="What’s the impact of the issue (multiple choice possible)",
    )
    priority = fields.Selection(
        help="If the issue is urgent, please call also directly the problem solve"
    )
    company_id = fields.Many2one(
        help="Will be assigned automatically based on Helpdesk "
        "Team selected by Helpdesk Manager"
    )
    product_id = fields.Many2one(
        help="Reference of main piece involved",
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )

    @api.depends("customer_id")
    def _compute_customer_name(self):
        for ticket in self:
            if ticket.customer_id:
                ticket.customer_name = ticket.customer_id.name

    @api.depends("customer_id")
    def _compute_customer_email(self):
        for ticket in self:
            if ticket.customer_id:
                ticket.customer_email = ticket.customer_id.email

    @api.model_create_multi
    def create(self, listvals):
        for vals in listvals:
            vals["ticket_number"] = self.env["ir.sequence"].next_by_code(
                "helpdesk.ticket"
            )
        return super().create(listvals)

    def default_get(self, fields):
        result = super().default_get(fields)
        if result.get("team_id") and fields:
            result.pop("team_id")
        return result


class HelpdeskTicketType(models.Model):
    _inherit = "helpdesk.ticket.type"

    is_show_customer_fields = fields.Boolean(
        default=True, string="Show Customer Fields"
    )
    help = fields.Char(translate=True)

    def name_get(self):
        res = []
        for x in self:
            name = x.name
            if x.help:
                name += " (%s)" % x.help
            res.append((x.id, name))
        return res

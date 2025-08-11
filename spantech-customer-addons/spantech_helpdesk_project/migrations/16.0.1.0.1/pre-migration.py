# Copyright 2009-2024 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import SUPERUSER_ID, api


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    tickets = env["helpdesk.ticket"].with_context(active_test=False).search([])
    for ticket in tickets:
        if ticket.impact_of_incident:
            ticket.description = (
                ticket.description + "\n" + ticket.impact_of_incident
                if ticket.description
                else ticket.impact_of_incident
            )

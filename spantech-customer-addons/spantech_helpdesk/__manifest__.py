# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech helpdesk",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "",
    "summary": " ",
    "depends": ["spantech_analytic", "helpdesk_repair"],
    "data": [
        "security/ir.model.access.csv",
        "data/ir.sequence.xml",
        "views/helpdesk_ticket.xml",
        "views/helpdsek.ticket.category.incident.xml",
        "views/helpdesk_ticket_reporter_views.xml",
    ],
    "installable": True,
}

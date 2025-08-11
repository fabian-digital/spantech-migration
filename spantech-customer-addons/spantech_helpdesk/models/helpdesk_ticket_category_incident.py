# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicketCategoryOfIncident(models.Model):
    _name = "helpdesk.ticket.category.incident"
    _description = "Helpdesk Ticket Category of incident"
    _order = "sequence, name"
    _rec_name = "name"

    name = fields.Char(string="Incident", required=True, translate=True)
    sequence = fields.Integer(default=10)
    help = fields.Char(translate=True)

    def name_get(self):
        res = []
        for x in self:
            name = x.name
            if x.help:
                name += " (%s)" % x.help
            res.append((x.id, name))
        return res

    _sql_constraints = [
        ("name_uniq", "unique (name)", "Category of incident already exists !"),
    ]

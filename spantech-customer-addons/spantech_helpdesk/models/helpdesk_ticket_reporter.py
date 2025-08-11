# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class HelpdeskTicketReporter(models.Model):
    _name = "helpdesk.ticket.reporter"
    _description = "Ticket Reporter"

    sequence = fields.Integer(default=10)
    name = fields.Char(string="Reporter", required=True, translate=True)
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
        ("name_uniq", "unique (name)", "Reporter name already exists !"),
    ]

# Copyright 2009-2025 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

from odoo import fields, models


class ConsolidationJournal(models.Model):
    _inherit = "consolidation.journal"

    line_ids = fields.One2many(copy=True)


class ConsolidationJournalLine(models.Model):
    _inherit = "consolidation.journal.line"

    period_id = fields.Many2one(ondelete="cascade")
    account_id = fields.Many2one(ondelete="cascade")

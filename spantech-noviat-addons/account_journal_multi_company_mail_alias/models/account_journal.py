# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.tools import remove_accents


def is_encodable_as_ascii(string):
    try:
        remove_accents(string).encode("ascii")
    except UnicodeEncodeError:
        return False
    return True


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _compute_alias_domain(self):
        for rec in self:
            rec.alias_domain = (
                rec.company_id.mail_alias_domain
                or super(AccountJournal, rec)._compute_alias_domain()
            )
        return

    def _inverse_type(self):
        for journal in self:
            alias_name = next(
                string
                for string in (
                    journal.alias_name,
                    journal.name,
                    journal.code,
                    journal.type,
                )
                if string and is_encodable_as_ascii(string)
            )
            super(AccountJournal, journal)._inverse_type()
            if journal.alias_id:
                if journal.alias_domain and journal.company_id != self.env.ref(
                    "base.main_company"
                ):
                    journal.alias_id.sudo().write({"alias_name": alias_name})
        self.invalidate_recordset(["alias_name"])
        return

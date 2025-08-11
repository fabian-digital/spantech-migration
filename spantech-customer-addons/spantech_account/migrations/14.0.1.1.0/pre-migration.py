# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        "SELECT indexname FROM pg_indexes WHERE indexname = %s",
        ("res_partner_bank_unique_shared_number",),
    )
    if cr.fetchone():
        cr.execute("DROP INDEX res_partner_bank_unique_shared_number")

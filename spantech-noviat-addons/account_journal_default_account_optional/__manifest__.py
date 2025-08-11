# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Default account optional on Sale/Purchase journals",
    "version": "16.0.1.0.0",
    "category": "Accounting & Finance",
    "summary": """
        This module makes the Default Account field optional for
        Sales and Purchase Journals
    """,
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "depends": ["account"],
    "data": ["views/account_journal_views.xml"],
    "installable": True,
    "license": "AGPL-3",
}

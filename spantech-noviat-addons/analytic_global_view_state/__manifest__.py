# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Analytic Global View - State",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Analytic",
    "depends": ["analytic_global_view"],
    "data": [
        "security/ir.model.access.csv",
        "views/analytic_account_account_state_views.xml",
        "views/account_analytic_account_views.xml",
    ],
    "installable": True,
}

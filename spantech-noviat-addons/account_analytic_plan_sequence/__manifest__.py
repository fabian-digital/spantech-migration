# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Account Analytic Plan Sequence",
    "version": "16.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Noviat",
    "license": "AGPL-3",
    "website": "https://www.noviat.com/",
    "depends": [
        "account",
    ],
    "data": [
        "views/account_analytic_plan_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_analytic_plan_sequence/static/src/components/**/*",
        ],
    },
    "application": False,
    "installable": True,
    "auto_install": False,
}

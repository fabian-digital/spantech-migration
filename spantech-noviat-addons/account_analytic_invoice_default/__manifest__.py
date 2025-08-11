# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Analytic Invoice Default",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Accounting & Finance",
    "summary": "Account Analytic Invoice Default",
    "depends": ["account", "analytic"],
    "data": [
        "views/account_move_views.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
}

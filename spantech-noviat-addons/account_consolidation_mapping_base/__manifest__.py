# Copyright 2009-2023 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

{
    "name": "Account Consolidation Mapping base module",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Accounting & Finance",
    "depends": ["account_consolidation"],
    "data": [
        "security/account_consolidation_security.xml",
        "security/ir.model.access.csv",
        "views/account_account_views.xml",
        "views/res_config_settings.xml",
    ],
    "installable": True,
}

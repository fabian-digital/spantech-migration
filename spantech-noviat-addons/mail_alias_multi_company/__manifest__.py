# Copyright 2022 Noviat (https://www.noviat.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

{
    "name": "Multi-company mail alias",
    "summary": """
    This module allows to set a different email domain per company.
    """,
    "version": "16.0.1.0.0",
    "category": "base",
    "author": "Noviat",
    "license": "AGPL-3",
    "website": "https://www.noviat.com/",
    "depends": ["mail"],
    "data": [
        "security/mail_alias_security.xml",
        "views/mail_alias_views.xml",
        "wizards/res_config_settings.xml",
    ],
}

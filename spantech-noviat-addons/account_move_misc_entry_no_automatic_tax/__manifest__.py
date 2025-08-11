# Copyright 2009-2023 Noviat.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Account Misc Entries - No automatic tax",
    "summary": "Do not set tax object when creating a miscellaneous accounting entry",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Accounting & Finance",
    "depends": ["account"],
    "installable": True,
    "pre_init_hook": "pre_init_hook",
}

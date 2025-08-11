# Copyright 2009-2022 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Partner",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "depends": ["spantech_base", "account", "partner_identification"],
    "installable": True,
    "data": [
        "views/res_partner_views.xml",
        "views/res_partner_industry_views.xml",
    ],
}

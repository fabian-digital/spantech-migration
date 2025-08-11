# Copyright 2009-2023 Noviat
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    "name": "Spantech Anglo-Saxon ITR Consolidation Entry",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Spantech",
    "complexity": "normal",
    "depends": ["account", "date_range", "spantech_intercompany"],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "wizards/spantech_anglo_saxon_conso_booking_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
}

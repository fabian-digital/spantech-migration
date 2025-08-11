# Copyright 2009-2022 Noviat (http://www.noviat.com).
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Tree dates search",
    "version": "16.0.1.0.0",
    "license": "AGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Hidden/Tools",
    "depends": [
        "web",
    ],
    "data": [
        "data/ir_config_parameter_data.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "web_tree_date_search/static/src/components/*/*.scss",
            "web_tree_date_search/static/src/components/*/*.js",
            "web_tree_date_search/static/src/components/*/*.xml",
        ],
    },
    "installable": True,
}

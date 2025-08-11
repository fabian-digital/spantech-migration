# Copyright 2009-2022 Noviat.
# License LGPL-3 or later (http://www.gnu.org/licenses/lpgl).

{
    "name": "OCA Financial Reports on Consolidation Accounts",
    "version": "16.0.1.0.0",
    "license": "LGPL-3",
    "author": "Noviat",
    "website": "https://www.noviat.com/",
    "category": "Accounting & Finance",
    "depends": [
        "account_consolidation_mapping_base",
        "account_financial_report",
    ],
    "data": [
        "wizards/general_ledger_report_wizard_views.xml",
        "wizards/trial_balance_report_wizard_views.xml",
    ],
    "installable": True,
}

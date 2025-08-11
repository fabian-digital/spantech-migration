# noinspection PyStatementEffect
{
    'name': 'Trilab PL Financial Reports',
    'summary': 'Trilab PL Financial Reports: Balance and P&L',
    'description': """
        Structure for the financial reports Balance and P&L according to polish account rules and in accordance
         to electronic reports for IRS.
    """,

    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'category': 'Accounting',
    'version': '16.0.6.0.0',
    'depends': ['account_reports', 'trilab_jpk_base'],
    'data': [
        'security/ir.model.access.csv',
        # Tags
        'data/trilab_accounting_tags.xml',
        # Reports
        'data/trilab_balance_sheet_report.xml',
        'data/trilab_pl_RZiSPor_report.xml',
        'data/trilab_pl_RZiSKalk_report.xml',
        'data/trilab_pl_CIT_report.xml',
        'report/journal.xml',
        'wizard/pl_journal.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 30.0,
    'currency': 'EUR',
}

# noinspection PyStatementEffect
{
    'name': 'Poland - Accounting (Trilab)',
    'description': 'Polish chart of accounts and taxes.',
    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'category': 'Accounting/Localizations/Account Charts',
    'version': '16.0.6.0.0',
    'depends': ['trilab_jpk_vat', 'trilab_pl_reports'],
    'data': [
        'data/l10n_pl_trilab_chart_data.xml',
        'data/trilab_tax_group_data.xml',
        'data/account.account.template.csv',
        'data/l10n_pl_trilab_chart_data_def.xml',
        'data/account.group.template.csv',
        'data/res.country.state.csv',
        'data/trilab_tax_data.xml',
        'data/account_fiscal_position_data.xml',        
        'data/account_chart_template_data.xml',
    ],
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1'
}

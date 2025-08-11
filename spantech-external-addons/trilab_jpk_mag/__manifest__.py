# noinspection PyStatementEffect
{
    'name': "Trilab JPK MAG",

    'summary': """
        Generate JPK MAG XML
        """,

    'description': """
        Report and generate XML for JPK (Jednolity Plik Kontrolny) Magazyn,
        required for accounting reporting in Poland
    """,

    'author': "Trilab",
    'website': "https://trilab.pl",

    'category': 'Accounting',
    'version': '16.0.1.0.2',

    'depends': [
        'purchase_stock',
        'sale_stock',
        'stock_landed_costs',
        'trilab_jpk_base',
    ],

    'data': [
        'security/ir.model.access.csv',
        'views/reports.xml',
        'views/stock_picking_type_views.xml',
        'wizard/jpk_mag_report_wizard.xml',
        'report/jpk_mag_report.xml',
    ],
    'images': [
        'static/description/banner.png'
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 240.0,
    'currency': 'EUR'
}

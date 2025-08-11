{
    'name': 'Trilab JPK FA',
    'summary': """
        Generate JPK FA XML
        """,
    'description': """
        Report and generate XML for JPK (Jednolity Plik Kontrolny) Faktury/Invoices,
        required for accounting reporting in Poland
    """,
    'author': 'Trilab',
    'website': 'https://trilab.pl',
    'category': 'Accounting',
    'version': '16.0.8.2.0',
    'depends': ['contacts', 'trilab_invoice', 'trilab_jpk_vat'],
    'data': ['security/ir.model.access.csv', 'data/data.xml', 'wizard/jpk_fa.xml'],
    'images': ['static/description/banner.png', 'static/description/scr1.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'price': 240.0,
    'currency': 'EUR',
}

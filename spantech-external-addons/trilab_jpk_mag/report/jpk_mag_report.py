import re
from collections import namedtuple
from datetime import datetime, timedelta

from lxml import etree

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools import float_repr

Section = namedtuple('Section', 'title,key,section_key')


class JpkMagReport(models.AbstractModel):
    _name = 'report.trilab_jpk_mag.jpk_mag_report'
    _inherit = 'jpk.trilab.export_helper'
    _description = 'JPK MAG Report'

    sections = {
        'PZ': {'title': 'Przyjęcie z zewnątrz', 'index': 'NumerPZ'},
        'PZWartosc': {
            'title': 'PZ Wartość',
            'columns': ['NumerPZ', 'DataPZ', 'WartoscPZ', 'DataOtrzymaniaPZ', 'Dostawca', 'NumerFaPZ', 'DataFaPZ'],
            'numbers': ['WartoscPZ'],
            'dates': ['DataPZ', 'DataOtrzymaniaPZ', 'DataFaPZ'],
            'optional': ['NumerFaPZ', 'DataFaPZ'],
        },
        'PZWiersz': {
            'title': 'PZ Wiersz',
            'columns': [
                'Numer2PZ',
                'KodTowaruPZ',
                'NazwaTowaruPZ',
                'IloscPrzyjetaPZ',
                'JednostkaMiaryPZ',
                'CenaJednPZ',
                'WartoscPozycjiPZ',
            ],
            'numbers': ['IloscPrzyjetaPZ', 'CenaJednPZ', 'WartoscPozycjiPZ'],
            'dates': [],
            'optional': ['KodTowaruPZ'],
        },
        'WZ': {'title': 'Wydanie na zewnątrz', 'index': 'NumerWZ'},
        'WZWartosc': {
            'title': 'WZ Wartość',
            'columns': ['NumerWZ', 'DataWZ', 'WartoscWZ', 'DataWydaniaWZ', 'OdbiorcaWZ', 'NumerFaWZ', 'DataFaWZ'],
            'numbers': ['WartoscWZ'],
            'dates': ['DataWZ', 'DataWydaniaWZ', 'DataFaWZ'],
            'optional': ['NumerFaWZ', 'DataFaWZ'],
        },
        'WZWiersz': {
            'title': 'WZ Wiersz',
            'columns': [
                'Numer2WZ',
                'KodTowaruWZ',
                'NazwaTowaruWZ',
                'IloscWydanaWZ',
                'JednostkaMiaryWZ',
                'CenaJednWZ',
                'WartoscPozycjiWZ',
            ],
            'numbers': ['IloscWydanaWZ', 'CenaJednWZ', 'WartoscPozycjiWZ'],
            'dates': [],
            'optional': ['KodTowaruWZ'],
        },
        'RW': {'title': 'Rozchód wewnętrzny', 'index': 'NumerRW'},
        'RWWartosc': {
            'title': 'RW Wartość',
            'columns': ['NumerRW', 'DataRW', 'WartoscRW', 'DataWydaniaRW', 'SkadRW', 'DokadRW'],
            'numbers': ['WartoscRW'],
            'dates': ['DataRW', 'DataWydaniaRW'],
            'optional': ['SkadRW', 'DokadRW'],
        },
        'RWWiersz': {
            'title': 'RW Wiersz',
            'columns': [
                'Numer2RW',
                'KodTowaruRW',
                'NazwaTowaruRW',
                'IloscWydanaRW',
                'JednostkaMiaryRW',
                'CenaJednRW',
                'WartoscPozycjiRW',
            ],
            'numbers': ['IloscWydanaRW', 'CenaJednRW', 'WartoscPozycjiRW'],
            'dates': [],
            'optional': ['KodTowaruRW'],
        },
        'MM': {'title': 'Przesunięcia międzymagazynowe', 'index': 'NumerMM'},
        'MMWartosc': {
            'title': 'MM Wartość',
            'columns': ['NumerMM', 'DataMM', 'WartoscMM', 'DataWydaniaMM', 'SkadMM', 'DokadMM'],
            'optional': ['SkadMM', 'DokadMM'],
            'dates': ['DataMM', 'DataWydaniaMM'],
        },
        'MMWiersz': {
            'title': 'MM Wiersz',
            'columns': [
                'Numer2MM',
                'KodTowaruMM',
                'NazwaTowaruMM',
                'IloscWydanaMM',
                'JednostkaMiaryMM',
                'CenaJednMM',
                'WartoscPozycjiMM',
            ],
            'numbers': ['IloscWydanaMM', 'CenaJednMM', 'WartoscPozycjiMM'],
            'dates': [],
            'optional': ['KodTowaruMM'],
        },
    }

    def _get_pz(self, options):
        # noinspection SqlResolve
        query = """
    SELECT sw.name                                                           AS Magazyn,
           sp.name                                                           AS NumerPZ,
           sp.create_date                                                    AS DataPZ,
           COALESCE(SUM(svl.value) OVER (PARTITION BY sp.id), 0)             AS WartoscPZ,
           sp.date_done                                                      AS DataOtrzymaniaPZ,
           rp.name                                                           AS Dostawca,
           am.name                                                           AS NumerFaPZ,
           am.invoice_date                                                   AS DataFaPZ,
           sp.name                                                           AS Numer2PZ,
           pp.default_code                                                   AS KodTowaruPZ,
           sm.name                                                           AS NazwaTowaruPZ,
           sm.product_uom_qty                                                AS IloscPrzyjetaPZ,
           um.name                                                           AS JednostkaMiaryPZ,
           COALESCE(svl.unit_cost, 0)                                        AS CenaJednPZ,
           COALESCE(svl.value, 0)                                            AS WartoscPozycjiPZ
    FROM stock_picking sp
             LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
             LEFT JOIN stock_warehouse sw ON sw.id = spt.warehouse_id
             LEFT JOIN res_partner rp ON sp.partner_id = rp.id
             LEFT JOIN stock_move sm ON sm.picking_id = sp.id
             LEFT JOIN product_product pp ON pp.id = sm.product_id
             LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
             LEFT JOIN uom_uom um ON um.id = sm.product_uom
             LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
             LEFT JOIN (SELECT DISTINCT ON (sp2.id) sp2.id sp_id, am.id am_id FROM stock_picking sp2
                             INNER JOIN stock_move sm2 on sp2.id = sm2.picking_id
                             INNER JOIN purchase_order_line pol ON sm2.purchase_line_id = pol.id
                             INNER JOIN account_move_line aml ON pol.id = aml.purchase_line_id
                             INNER JOIN account_move am ON aml.move_id = am.id) sp_am_rel ON sp.id = sp_am_rel.sp_id
             LEFT JOIN account_move am ON sp_am_rel.am_id = am.id
    WHERE sp.state = 'done'
      AND sm.state = 'done'
      AND spt.x_jpk_mag = 'JPK_PZ'
      AND sp.date_done >= %s
      AND sp.date_done < %s
      AND sw.id = %s
      AND sp.company_id = %s --spółka
      AND pt.type = 'product'
    """
        warehouse = options.get('warehouse_id')
        warehouse = warehouse if isinstance(warehouse, int) else None

        params = (
            fields.Datetime.from_string(options.get('date_from')),
            fields.Datetime.from_string(options.get('date_to')) + timedelta(days=1),
            warehouse,
            self.env.company.id,
        )
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _get_wz(self, options):
        # noinspection SqlResolve
        query = """SELECT
           sw.name                                                            AS Magazyn,
           sp.name                                                            AS NumerWZ,
           sp.create_date                                                     AS DataWZ,
           COALESCE(-SUM(svl.value) OVER (PARTITION BY sp.id), 0)             AS WartoscWZ,
           sp.date_done                                                       AS DataWydaniaWZ,
           rp.name                                                            AS OdbiorcaWz,
           am.name                                                            AS NumerFaWZ,
           am.invoice_date                                                    AS DataFaWZ,
           sp.name                                                            AS Numer2WZ,
           pp.default_code                                                    AS KodTowaruWZ,
           sm.name                                                            AS NazwaTowaruWZ,
           sm.product_uom_qty                                                 AS IloscWydanaWZ,
           um.name                                                            AS JednostkaMiaryWZ,
           COALESCE(svl.unit_cost, 0)                                        AS CenaJednWZ,
           COALESCE(-svl.value, 0)                                            AS WartoscPozycjiWZ
    FROM stock_picking sp
             LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
             LEFT JOIN stock_warehouse sw ON sw.id = spt.warehouse_id
             LEFT JOIN res_partner rp ON sp.partner_id = rp.id
             LEFT JOIN stock_move sm ON sm.picking_id = sp.id
             LEFT JOIN product_product pp ON pp.id = sm.product_id
             LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
             LEFT JOIN uom_uom um ON um.id = sm.product_uom
             LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
             LEFT JOIN (SELECT DISTINCT ON (so2.id) so2.id so_id, am2.id am_id FROM sale_order so2
                             INNER JOIN sale_order_line sol ON so2.id = sol.order_id
                             INNER JOIN sale_order_line_invoice_rel sol_inv_rel ON sol.id = sol_inv_rel.order_line_id
                             INNER JOIN account_move_line aml ON sol_inv_rel.invoice_line_id = aml.id
                             INNER JOIN account_move am2 ON am2.id = aml.move_id) so_am_rel ON sp.sale_id = so_am_rel.so_id
             LEFT JOIN account_move am ON am.id = so_am_rel.am_id
    WHERE sp.state = 'done'
      AND sm.state = 'done'
      AND spt.x_jpk_mag = 'JPK_WZ'
      AND sp.date_done >= %s
      AND sp.date_done < %s
      AND sw.id = %s            --par magazyn
      AND sp.company_id = %s --spółka
      AND pt.type = 'product'
    """
        warehouse = options.get('warehouse_id')
        warehouse = warehouse if isinstance(warehouse, int) else None

        params = (
            fields.Datetime.from_string(options.get('date_from')),
            fields.Datetime.from_string(options.get('date_to')) + timedelta(days=1),
            warehouse,
            self.env.company.id,
        )
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _get_rw(self, options):
        # noinspection SqlResolve
        query = """SELECT
           sw.name                                                            AS Magazyn,
           sp.name                                                            AS NumerRW,
           sp.create_date                                                     AS DataRW,
           COALESCE(-SUM(svl.value) OVER (PARTITION BY sp.id), 0)             AS WartoscRW,
           sp.date_done                                                       AS DataWydaniaRW,
           sw.name                                                            AS SkadRW,
           NULL                                                               AS DokadRW,
           sp.name                                                            AS Numer2RW,
           pp.default_code                                                    AS KodTowaruRW,
           sm.name                                                            AS NazwaTowaruRW,
           sm.product_uom_qty                                                 AS IloscWydanaRW,
           um.name                                                            AS JednostaMiaryRW,
           COALESCE(svl.unit_cost, 0)                                         AS CenaJednRW,
           COALESCE(-svl.value, 0)                                            AS WartoscPozycjiRW
    FROM stock_picking sp
             LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
             LEFT JOIN stock_warehouse sw ON sw.id = spt.warehouse_id
             LEFT JOIN res_partner rp ON sp.partner_id = rp.id
             LEFT JOIN stock_move sm ON sm.picking_id = sp.id
             LEFT JOIN product_product pp ON pp.id = sm.product_id
             LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
             LEFT JOIN uom_uom um ON um.id = sm.product_uom
             LEFT JOIN stock_valuation_layer svl ON sm.id = svl.stock_move_id
    WHERE sp.state = 'done'
      AND sm.state = 'done'
      AND spt.x_jpk_mag = 'JPK_RW'
      AND sp.date_done >= %s
      AND sp.date_done < %s
      AND sw.id = %s            --par magazyn
      AND sp.company_id = %s --spółka
      AND pt.type = 'product'
    """
        warehouse = options.get('warehouse_id')
        warehouse = warehouse if isinstance(warehouse, int) else None

        params = (
            fields.Datetime.from_string(options.get('date_from')),
            fields.Datetime.from_string(options.get('date_to')) + timedelta(days=1),
            warehouse,
            self.env.company.id,
        )
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _get_mm(self, options):
        # noinspection SqlResolve
        query = """SELECT
           sw.name                                                            AS Magazyn,
           sp.name                                                            AS NumerMM,
           sp.create_date                                                     AS DataMM,
           COALESCE(SUM(standard_price_property.value_float * sm.product_uom_qty) OVER (PARTITION BY sp.id), 0) 
                                                                              AS WartoscMM,
           sp.date_done                                                       AS DataWydaniaMM,
           sl.complete_name                                                   AS SkadMW,
           sld.complete_name                                                  AS DokadMM,
           sp.name                                                            AS Numer2MM,
           pp.default_code                                                    AS KodTowaruMM,
           sm.name                                                            AS NazwaTowaruMM,
           sm.product_uom_qty                                                 AS IloscWydanaMM,
           um.name                                                            AS JednostaMiaryMM,
           COALESCE(standard_price_property.value_float, 0)                                 AS CenaJednMM,
           COALESCE(standard_price_property.value_float * sm.product_uom_qty, 0)            AS WartoscPozycjiMM
    FROM stock_picking sp
             LEFT JOIN stock_picking_type spt ON spt.id = sp.picking_type_id
             LEFT JOIN stock_warehouse sw ON sw.id = spt.warehouse_id
             LEFT JOIN res_partner rp ON sp.partner_id = rp.id
             LEFT JOIN stock_move sm ON sm.picking_id = sp.id
             LEFT JOIN product_product pp ON pp.id = sm.product_id
             LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
             LEFT JOIN uom_uom um ON um.id = sm.product_uom
             LEFT JOIN stock_location sl ON sl.id = sp.location_id
             LEFT JOIN stock_location sld ON sld.id = sp.location_dest_id
             LEFT JOIN ir_property standard_price_property
                   ON (standard_price_property.res_id = 'product.product,' || pp.id AND
                       standard_price_property.name = 'standard_price' AND
                       standard_price_property.company_id = %s)
    WHERE sp.state = 'done'
      AND sm.state = 'done'
      AND spt.x_jpk_mag = 'JPK_MM'
      AND sp.date_done >= %s
      AND sp.date_done < %s
      AND sw.id = %s            --par magazyn
      AND sp.company_id = %s --spółka
      AND pt.type = 'product'
    """
        warehouse = options.get('warehouse_id')
        warehouse = warehouse if isinstance(warehouse, int) else None

        params = (
            self.env.company.id,
            fields.Datetime.from_string(options.get('date_from')),
            fields.Datetime.from_string(options.get('date_to')) + timedelta(days=1),
            warehouse,
            self.env.company.id,
        )
        self.env.cr.execute(query, params)
        return self.env.cr.dictfetchall()

    def _get_section_columns_name(self, section_name):
        return [x for x in self.sections[section_name]['columns']]

    @api.model
    def _get_section_lines(self, options, section_name, data):
        lines = []

        lang = options['lang']

        for row in data:
            new_line = {'columns': [row.get(k.lower()) for k in self.sections[section_name]['columns']]}
            for idx, column in enumerate(self.sections[section_name]['columns']):
                if column in self.sections[section_name]['numbers']:
                    value = new_line['columns'][idx]
                    new_line['columns'][idx] = float_repr(value, 2) if value else value

            # Get translated value
            for idx, col in enumerate(new_line['columns']):
                if isinstance(col, dict) and lang in col:
                    new_line['columns'][idx] = col[lang]

            lines.append(new_line)

        return lines

    @api.model
    def _get_report_data(self, docids, options):
        data = {'sections': {}, 'mapping': []}

        for section_name in ('PZ', 'WZ', 'RW', 'MM'):
            section_data = getattr(self, f'_get_{section_name.lower()}')(options)

            section_value_key = f'section_{section_name.lower()}_value'
            section_value_name = f'{section_name}Wartosc'

            section_row_key = f'section_{section_name.lower()}_row'
            section_row_name = f'{section_name}Wiersz'

            data['sections'].update(
                {
                    section_value_key: {
                        'columns_header': self._get_section_columns_name(section_value_name),
                        'lines': self._get_section_lines(options, section_value_name, data=section_data),
                    },
                    section_row_key: {
                        'columns_header': self._get_section_columns_name(section_row_name),
                        'lines': self._get_section_lines(options, section_row_name, data=section_data),
                    },
                }
            )

            data['mapping'].extend(
                [
                    Section(
                        title=self.sections[section_value_name]['title'],
                        key=section_value_key,
                        section_key=section_value_name,
                    ),
                    Section(
                        title=self.sections[section_row_name]['title'],
                        key=section_row_key,
                        section_key=section_row_name,
                    ),
                ]
            )

        return data

    def _get_report_values(self, docids, data):
        company = self.env['res.company'].browse(data['company_id'])

        report_data = self._get_report_data(docids=docids, options=data)

        return {
            'company_name': company.display_name,
            'currency_name': company.currency_id.name,
            'date_to': data['date_to'],
            'date_from': data['date_from'],
            'doc': report_data,
        }

    def get_xml(self, options):
        tns = 'http://jpk.mf.gov.pl/wzor/2016/03/09/03093/'
        # noinspection HttpUrlsUsage
        tns_etd = "http://crd.gov.pl/xml/schematy/dziedzinowe/mf/2016/01/25/eD/DefinicjeTypy/"
        company = self.env.company

        lang = options['lang']

        jpk = etree.Element(etree.QName(tns, 'JPK'), nsmap={'tns': tns, 'etd': tns_etd})
        header = etree.SubElement(jpk, etree.QName(tns, 'Naglowek'))

        etree.SubElement(
            header, etree.QName(tns, 'KodFormularza'), attrib={'kodSystemowy': 'JPK_MAG (1)', 'wersjaSchemy': '1-0'}
        ).text = 'JPK_MAG'
        etree.SubElement(header, etree.QName(tns, 'WariantFormularza')).text = '1'
        etree.SubElement(header, etree.QName(tns, 'CelZlozenia')).text = '1'
        etree.SubElement(header, etree.QName(tns, 'DataWytworzeniaJPK')).text = fields.Datetime.now().isoformat()
        etree.SubElement(header, etree.QName(tns, 'DataOd')).text = (
            options['date_from'] if isinstance(options['date_from'], str) else str(options['date_from'])
        )
        etree.SubElement(header, etree.QName(tns, 'DataDo')).text = (
            options['date_to'] if isinstance(options['date_to'], str) else str(options['date_to'])
        )
        etree.SubElement(header, etree.QName(tns, 'DomyslnyKodWaluty')).text = company.currency_id.name

        if not company.pl_tax_office_id:
            raise UserError(_('Tax Office is not set for the company'))

        etree.SubElement(header, etree.QName(tns, 'KodUrzedu')).text = company.pl_tax_office_id.code

        podmiot = etree.SubElement(jpk, etree.QName(tns, 'Podmiot1'))
        ident_podmiot = etree.SubElement(podmiot, etree.QName(tns, 'IdentyfikatorPodmiotu'))
        etree.SubElement(ident_podmiot, etree.QName(tns_etd, 'NIP')).text = re.sub(r'\D', '', company.vat)
        etree.SubElement(ident_podmiot, etree.QName(tns_etd, 'PelnaNazwa')).text = company.name[:240]

        if company.company_registry:
            etree.SubElement(ident_podmiot, etree.QName(tns_etd, 'REGON')).text = company.company_registry

        address_podmiot = etree.SubElement(podmiot, etree.QName(tns, 'AdresPodmiotu'))
        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'KodKraju')).text = company.country_id.code
        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Wojewodztwo')).text = company.state_id.name

        if company.pl_county:
            etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Powiat')).text = company.pl_county
        else:
            raise UserError(_('County is not set for company'))

        if company.pl_community:
            etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Gmina')).text = company.pl_community
        else:
            raise UserError(_('Community is not set for company'))

        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Ulica')).text = company.x_street_short
        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'NrDomu')).text = company.x_street_short_number or 'brak'

        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Miejscowosc')).text = company.city
        etree.SubElement(address_podmiot, etree.QName(tns_etd, 'KodPocztowy')).text = company.zip

        if company.pl_post:
            etree.SubElement(address_podmiot, etree.QName(tns_etd, 'Poczta')).text = company.pl_post
        else:
            raise UserError(_('Post is not set for company'))

        warehouse_id = self.env['stock.warehouse'].browse(options['warehouse_id'])

        if warehouse_id is None:
            raise UserError(_('Warehouse is not selected'))

        etree.SubElement(jpk, etree.QName(tns, 'Magazyn')).text = warehouse_id.name

        for section in ('PZ', 'WZ', 'RW', 'MM'):
            master_section = None

            section_data = getattr(self, f'_get_{section.lower()}')(options)

            if section_data:
                master_section = etree.SubElement(jpk, etree.QName(tns, section))

            doc_ids = set()
            section_counters = {'lines': 0, 'SumaPZ': 0.0, 'Suma': 0.0}

            for subsection in ('Wartosc', 'Wiersz'):
                subsection_name = f'{section}{subsection}'
                for line in section_data:
                    # prevent from creating multiple 'Wartosc' section for one document
                    doc_id = line.get(self.sections[section]['index'].lower())
                    if subsection == 'Wartosc' and doc_id in doc_ids:
                        continue
                    elif subsection == 'Wartosc':
                        doc_ids.add(doc_id)

                    section_element = etree.SubElement(master_section, etree.QName(tns, subsection_name))

                    section_counters['lines'] += 1

                    summaries = ()

                    if subsection == 'Wartosc':
                        if section == 'PZ':
                            summaries = (('wartoscpz', 'Suma'),)
                        elif section == 'WZ':
                            summaries = (('wartoscwz', 'Suma'),)
                        elif section == 'WZ':
                            summaries = (('wartoscrw', 'Suma'),)
                        elif section == 'WZ':
                            summaries = (('wartoscww', 'Suma'),)

                    for detail, summary in summaries:
                        value = line.get(detail)
                        if not value:
                            value = 0.0
                        section_counters[summary] += value

                    for field in self.sections[subsection_name]['columns']:
                        field_name = field.lower()
                        value = line.get(field_name)

                        if value is None and field in self.sections[subsection_name]['optional']:
                            continue
                        if field in self.sections[subsection_name]['numbers']:
                            value = value if value else 0
                            value = float_repr(value, 2)
                        elif field in self.sections[subsection_name]['dates']:
                            if isinstance(value, datetime):
                                value = value.date()
                            value = value.isoformat()
                        elif isinstance(value, dict) and lang in value:
                            value = str(value[lang])
                        else:
                            value = str(value)

                        etree.SubElement(section_element, etree.QName(tns, field)).text = value

            if section_counters['lines'] > 0:
                if section == 'PZ':
                    section_element = etree.SubElement(master_section, etree.QName(tns, 'PZCtrl'))
                    etree.SubElement(section_element, etree.QName(tns, 'LiczbaPZ')).text = str(
                        section_counters['lines']
                    )
                    etree.SubElement(section_element, etree.QName(tns, 'SumaPZ')).text = float_repr(
                        section_counters['Suma'], 2
                    )
                elif section == 'WZ':
                    section_element = etree.SubElement(master_section, etree.QName(tns, 'WZCtrl'))
                    etree.SubElement(section_element, etree.QName(tns, 'LiczbaWZ')).text = str(
                        section_counters['lines']
                    )
                    etree.SubElement(section_element, etree.QName(tns, 'SumaWZ')).text = float_repr(
                        section_counters['Suma'], 2
                    )
                elif section == 'RW':
                    section_element = etree.SubElement(master_section, etree.QName(tns, 'RWCtrl'))
                    etree.SubElement(section_element, etree.QName(tns, 'LiczbaRW')).text = str(
                        section_counters['lines']
                    )
                    etree.SubElement(section_element, etree.QName(tns, 'SumaRW')).text = float_repr(
                        section_counters['Suma'], 2
                    )
                elif section == 'WW':
                    section_element = etree.SubElement(master_section, etree.QName(tns, 'WWCtrl'))
                    etree.SubElement(section_element, etree.QName(tns, 'LiczbaWW')).text = str(
                        section_counters['lines']
                    )
                    etree.SubElement(section_element, etree.QName(tns, 'SumaWW')).text = float_repr(
                        section_counters['Suma'], 2
                    )

        return etree.tostring(jpk, encoding='UTF-8', xml_declaration=True, pretty_print=True)

    def transfer_xml(self, options):
        date = options.get('date_from')

        # noinspection PyUnresolvedReferences
        transfer_id = self.env['jpk.transfer'].create_with_document(
            {
                'name': f'JPK MAG {date}',
                'jpk_type': 'JPKAH',
                'file_name': f'jpk_mag_{date}.xml',
                'data': self.get_xml(options),
                'document_type': 'trilab_jpk_base.jpk_mag_doc_type',
            }
        )

        # noinspection PyUnresolvedReferences
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jpk.transfer',
            'view_mode': 'form',
            'res_id': transfer_id.id,
        }

    def generate_xml_report(self, file_data, doc_ids, options):
        file_data.write(self.get_xml(options))

    @api.model
    def _get_report_name(self):
        return _('Jednolity Plik Kontrolny - MAG')

    def generate_xlsx_report(self, workbook, doc_ids, options):
        # self.generate_xlsx_styles(workbook)
        data = self._get_report_data(doc_ids, options)
        sheet = workbook.add_worksheet(self._get_report_name()[:31])

        y_offset = 0

        # Set the first column width to 20
        sheet.set_column(0, 0, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 50)
        sheet.set_column(4, 4, 25)
        sheet.set_column(5, 8, 15)
        sheet.set_column(14, 14, 10)

        for section in data['mapping']:
            self._write_cell(sheet, y_offset, 0, section.title, style='title')
            y_offset += 1
            for h_col_idx, h_col in enumerate(data['sections'][section.key]['columns_header']):
                self._write_cell(sheet, y_offset, h_col_idx, h_col, style='title')

            y_offset += 1

            section_def = self.sections[section.section_key]
            section_def_cols = section_def['columns']

            for line in data['sections'][section.key]['lines']:
                for col_idx, (col_val, col_name) in enumerate(zip(line['columns'], section_def_cols)):
                    if col_name in section_def['dates']:
                        self._write_cell(sheet, y_offset, col_idx, col_val, style='default_date')
                    elif col_name in section_def['numbers']:
                        self._write_cell(sheet, y_offset, col_idx, float(col_val))
                    else:
                        self._write_cell(sheet, y_offset, col_idx, col_val)
                y_offset += 1

            y_offset += 1

import datetime
import logging

import requests
from dateutil.relativedelta import relativedelta

from odoo import models

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    _inherit = 'res.company'

    def _parse_nbp_data(self, available_currencies):
        """This method is used to update the currencies by using NBP (National Polish Bank) service API.
        Rates are given against PLN.
        """

        # this is url to fetch active (at the moment of fetch) average currency exchange table
        request_url = 'https://api.nbp.pl/api/exchangerates/tables/{}/?format=json'
        requested_currency_codes = available_currencies.mapped('name')
        result = {}

        # there are 3 tables with currencies:
        #   A - most used ones average,
        #   B - exotic currencies average,
        #   C - common bid/sell
        # we will parse first one and if there are unmatched currencies, proceed with second one

        for table_type in ['A', 'B']:
            if not requested_currency_codes:
                break

            response = requests.get(request_url.format(table_type), timeout=10)
            response.raise_for_status()
            response_data = response.json()

            for exchange_table in response_data:
                # there *should not be* be more than one table in response, but let's be on the safe side
                # and parse this in a loop as response is a list

                # effective date of this table
                table_date = datetime.datetime.strptime(exchange_table['effectiveDate'], '%Y-%m-%d').date()

                # for tax purpose, polish companies must use rate of day before transaction
                # this is achieved by offsetting the rate date by one day
                table_date += relativedelta(days=1)

                # add base currency
                if 'PLN' not in result and 'PLN' in requested_currency_codes:
                    result['PLN'] = (1.0, table_date, exchange_table['no'])

                for rec in exchange_table['rates']:
                    if rec['code'] in requested_currency_codes:
                        result[rec['code']] = (1.0 / rec['mid'], table_date, exchange_table['no'])
                        requested_currency_codes.remove(rec['code'])

        return result

    def _generate_currency_rates(self, parsed_data):
        super()._generate_currency_rates({k: v[:2] for k, v in parsed_data.items()})

        for company in self:
            for currency, (rate, date_rate, *extra) in parsed_data.items():
                if extra:
                    self.env['res.currency.rate'].search(
                        [('currency_id.name', '=', currency), ('name', '=', date_rate), ('company_id', '=', company.id)]
                    ).write({'x_nbp_table': extra[0]})

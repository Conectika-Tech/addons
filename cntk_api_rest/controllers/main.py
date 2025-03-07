# -*- coding: utf-8 -*-
from odoo import http
import json
from odoo.http import request
import logging


class HttpIntegrateController(http.Controller):
    _logger = logging.getLogger(__name__)

    def _prepare_response(self, status, message, data):
        return {
            'status': status,
            'message': message,
            'data': data
        }

    def _search_records(self, model, domain):
        return request.env[model].search(domain)

    def _prepare_order_json(self, order):
        return {
            'id': order.id,
            'user_id': order.user_id.id,
            'name': order.name,
            'date_order': order.date_order,
            'partner_id': order.partner_id.id,
            'partner_name': order.partner_id.name,
            'amount_total': order.amount_total,
            'state': order.state,
            'order_line': [
                {
                    'product_id': line.product_id.id,
                    'product_name': line.product_id.name,
                    'price_unit': line.price_unit,
                    'product_uom_qty': line.product_uom_qty,
                    'price_subtotal': line.price_subtotal,
                } for line in order.order_line
            ]
        }

    @http.route('/costumers', type='json', auth='user', methods=['GET'], csrf=False)
    def costumers(self, **kwargs):
        name = kwargs.get('name')
        self._logger.info(f"costumer: {name}")
        domain = [('customer_rank', '>', 0)]
        if name:
            domain.append(('name', 'ilike', name))
        customers = self._search_records('res.partner', domain)
        customersjson = [{'id': customer.id, 'name': customer.name, 'rfc': customer.vat} for customer in customers]
        return self._prepare_response('success', 'API request received with authentication cookie session_id', {'customers': customersjson})

    @http.route('/products', type='json', auth='user', methods=['GET'], csrf=False)
    def products(self, **kwargs):
        name = kwargs.get('name')
        self._logger.info(f"product: {name}")
        domain = [('sale_ok', '=', True)]
        if name:
            domain.append(('name', 'ilike', name))
        products = self._search_records('product.product', domain)
        productsjson = [{'id': product.id, 'name': product.name} for product in products]
        return self._prepare_response('success', 'API request received with authentication cookie session_id', {'products': productsjson})

    @http.route('/order', type='json', auth='user', methods=['POST'], csrf=False)
    def create_order(self, **kwargs):
        self._logger.info(f"create_order: {kwargs}")
        if kwargs:
            response = http.request.env['sale.order'].sudo().create(kwargs)
        return self._prepare_response('success', 'Order created successfully', {'order_id': response.id})

    @http.route('/order', type='json', auth='user', methods=['GET'], csrf=False)
    def search_order(self, **kwargs):
        self._logger.info(f"order: {kwargs}")
        query = []
        if 'id' in kwargs:
            query.append(('id', '=', kwargs['id']))
        if 'user_id' in kwargs:
            query.append(('user_id', '=', kwargs['user_id']))
        if 'partner_id' in kwargs:
            query.append(('partner_id', '=', kwargs['partner_id']))
        if 'name' in kwargs:
            query.append(('name', 'ilike', kwargs['name']))
        if 'from' in kwargs and 'to' in kwargs:
            query.append(('create_date', '>=', kwargs['from']))
            query.append(('create_date', '<=', kwargs['to']))
        self._logger.info(query)
        orders = self._search_records('sale.order', query)
        ordersjson = [self._prepare_order_json(order) for order in orders]
        return self._prepare_response('success', 'API request received with authentication cookie session_id', {'orders': ordersjson})

    @http.route('/pruebasa', type='json', auth='public', methods=['GET'], csrf=False)
    def pruebasa(self, **kwargs):
        parameters = json.loads(http.request.httprequest.data)
        return self._prepare_response('success', 'API PUBLIC request', {'parameters': parameters})
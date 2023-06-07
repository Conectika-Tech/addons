from odoo import fields, models, api
from datetime import datetime

import logging
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _logger = logging.getLogger(__name__)
    _inherit = 'res.partner'

    def cdi_downloader_wizard(self):
        return {
            'type' : 'ir.actions.act_window',
            'res_model' : 'cfdi.downloader.wizard',
            'name' : 'Descarga Masiva',
            'view_mode' : 'form',
            'target' : 'new',
            'context': {'default_partner_id': self.id},
        }
    
    def del_old_zips(self, context=None):
        today = datetime.now()
        customers = self.env['res.partner'].search([('customer_rank', '>', 0)])
        self._logger.info('----len clientes-----'+str(len(customers)))
        for customer in customers:
            atts = self.env['ir.attachment'].search([('res_model','=','res.partner'), ('res_id','=', customer.id)])
            if len(atts) > 0:
                self._logger.info('-------se jecuto -------'+customer.name+'  '+str(len(atts)))
                for att in atts:
                    diff = (today-att.create_date).days
                    if (att.name.find('Vrfcs')>-1 or att.name.find('Fctrs')>-1) and (diff > 31):
                        self._logger.info('diff...............'+str(diff))
                        self._logger.info('BORRAR***********'+att.name+'.. create date'+str(att.create_date))
                        att.unlink()
                        


        
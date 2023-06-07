    # -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError

import logging
from datetime import datetime
import base64
import os
import tempfile
import zipfile
import random

class cfdiDownloader(models.TransientModel):
    _logger = logging.getLogger(__name__)
    _name = 'cfdi.downloader.wizard'
    _description = 'CDFI Descarga'

    date_from = fields.Date(string="Fecha inicio", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="Fecha fin", required=True, default=fields.Date.context_today)
    tipo = fields.Selection([
        ('F', 'Facturas')
    ], required=True, string="Tipo Descarga", default='F')
    partner_id = fields.Many2one('res.partner', string='Cliente', change_default=True,
        readonly=True, help="You can find a contact by its Name, TIN, Email or Internal Reference.")

    zip_temp = fields.Binary(string='Cfdi zip content', copy=False, readonly=True)

    def get_zip(self):
        att_zip = False
        if  self.tipo=='F':
            self._logger.info('######### F')
            att_zip = self.search_fac()
        if att_zip:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/%s/?download=true' % (att_zip.id),
                'target': 'new',
            }
        else:
            raise UserError("Se intento la descarga de más de un mes de facturación o la búsqueda no arrojo ningun resultado")
    
    def search_fac(self):
        self._logger.info('######### ENTRO A FACTURAS')
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(self.date_from), fmt)
        d2 = datetime.strptime(str(self.date_to), fmt)
        self._logger.info('-----------dias-------'+str((d2-d1).days))
        if ((d2-d1).days>31): 
            return False
        invoices = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),('invoice_date', '>=',self.date_from),('invoice_date', '<=', self.date_to),('state', '=', 'posted')])
        self._logger.info(str(len(invoices)))
        myTemp = os.path.join(tempfile.gettempdir(),'val'+str(random.random()))
        zipName = "val" + str(random.random())+".zip"
        self._logger.info('############################ '+myTemp+zipName)
        z = zipfile.ZipFile(myTemp+zipName, "w")
        for inv in invoices:
            atts = self.env['ir.attachment'].search([('res_model','=','account.move'), ('res_id','=', inv.id)])
            for att in atts:
                if att.mimetype == 'application/pdf' or att.mimetype == 'application/xml':
                    z.write(att._full_path(att.store_fname), arcname = str(att.id)+'_'+att.name)
        z.close()
        with open(z.filename, "rb") as f:
            datas = (base64.b64encode(f.read())).decode('ascii')
        attname = 'Fctrs_'+self.partner_id.name + '_' + datetime.now().strftime("%d-%m-%Y")
        res = self.env['ir.attachment'].sudo().create({
                'name': attname,
                'datas': datas,
                'type': 'binary',
                'store_fname': attname +'.zip',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'mimetype': 'application/zip'
        })
        os.remove(z.filename)
        return res
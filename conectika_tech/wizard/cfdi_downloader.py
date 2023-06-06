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
import shutil

class cfdiDownloader(models.TransientModel):
    _logger = logging.getLogger(__name__)
    _name = 'cfdi.downloader.wizard'
    _description = 'CDFI Descarga'

    date_from = fields.Date(string="Fecha inicio", required=True, default=fields.Date.context_today)
    date_to = fields.Date(string="Fecha fin", required=True, default=fields.Date.context_today)
    tipo = fields.Selection([
        ('F', 'Facturas'),
        ('V', 'Validaciones SAT'),
    ], required=True, string="Tipo Descarga")
    partner_id = fields.Many2one('res.partner', string='Cliente', change_default=True,
        readonly=True, help="You can find a contact by its Name, TIN, Email or Internal Reference.")
    l10n_mx_edi_cfdi = fields.Binary(string='Cfdi content', copy=False, readonly=True)
    zip_temp = fields.Binary(string='Cfdi zip content', copy=False, readonly=True)

    def get_zip(self):
        att_zip = False
        if  self.tipo=='F':
            self._logger.info('######### F')
            att_zip = self.search_fac()
        elif self.tipo=='V':
            self._logger.info('######### V')
            att_zip = self.search_val()    
        self._logger.info('Q LLEGA ANTES DE LA REDIRR##################################')
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
        invoices = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),('invoice_date', '>=',self.date_from),('invoice_date', '<=', self.date_to),('state', '=', 'posted'),('l10n_mx_edi_sat_status', '=', 'valid')])
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
        

    def search_val(self):
        self._logger.info('######### ENTRO A VALIDACIONES')
        fmt = '%Y-%m-%d'
        d1 = datetime.strptime(str(self.date_from), fmt)
        d2 = datetime.strptime(str(self.date_to), fmt)
        self._logger.info('-------------dias---------'+str((d2-d1).days))
        if ((d2-d1).days>31): 
            return False
        invoices = self.env['account.move'].search([('partner_id', '=', self.partner_id.id),('invoice_date', '>=',self.date_from),('invoice_date', '<=', self.date_to),('state', '=', 'posted'),('l10n_mx_edi_sat_status', '=', 'valid')])
        self._logger.info(str(len(invoices)))
        myTemp = os.path.join(tempfile.gettempdir(),'val'+str(random.random()))
        self._logger.info('############################ '+myTemp)
        os.makedirs(myTemp)
        zipName = "val" + str(random.random())
        zipPath = os.path.join(tempfile.gettempdir(), zipName)
        z = zipfile.ZipFile(myTemp+zipName, "w")
        if(len(invoices)<1):
            return False
        for inv in invoices:
            cfdi = inv._l10n_mx_edi_decode_cfdi()
            if cfdi:
                rfcemisor = cfdi.get('supplier_rfc')
                nombreemisor = cfdi.get('cfdi_node').Emisor.get('Nombre').replace('Á','&Acute;').replace('É','&Eacute;').replace('Í','&Iacute;').replace('Ó','&Oacute;').replace('Ú','&Uacute;')
                rfcreceptor = cfdi.get('customer_rfc')
                nombrereceptor = cfdi.get('cfdi_node').Receptor.get('Nombre').replace('Á','&Acute;').replace('É','&Eacute;').replace('Í','&Iacute;').replace('Ó','&Oacute;').replace('Ú','&Uacute;')
                uuid = cfdi.get('uuid')
                fechaem = cfdi.get('cfdi_node').get('Fecha')
                fechatimbre = cfdi.get('stamp_date')
                pac = "htttps://conectika.tech"
                total = cfdi.get('amount_total')
                tipo = 'Ingreso' if cfdi.get('cfdi_node').get('TipoDeComprobante')=='I' else 'Egreso' if cfdi.get('cfdi_node').get('TipoDeComprobante')=='E' else cfdi.get('cfdi_node').get('TipoDeComprobante')
                vig = 'Vigente' if inv.l10n_mx_edi_sat_status=='valid' else inv.l10n_mx_edi_sat_status
                estatus = 'Cancelable con motivo' if inv.l10n_mx_edi_sat_status=='valid' else 'No cancelable'
                #llenar template
                html = self.template.format(rfcemisor=rfcemisor,nombreemisor=nombreemisor,rfcreceptor=rfcreceptor,nombrereceptor=nombrereceptor,uuid=uuid,fechaem=fechaem,fechatimbre=fechatimbre,pac=pac,total=total,tipo=tipo,vig=vig,estatus=estatus)
                fname = 'INV-'+inv.name.replace("/", "")+'-MX-Verification'
                filename = os.path.join(myTemp, fname+'.html')
                html_file = open(filename,"w")
                html_file.write(html)
                html_file.close()
                os.system('wkhtmltopdf '+filename+' '+myTemp+'/'+fname+'.pdf')
                os.remove(filename)
        z = shutil.make_archive(zipPath, 'zip', myTemp)
        if z:
            self._logger.error('  Z EXISTE---------------'+z)
            shutil.rmtree(myTemp)
            
        with open(z, "rb") as f:
            datas = (base64.b64encode(f.read())).decode('ascii')
        
        attname = 'Vrfcs_'+self.partner_id.name + '_' + datetime.now().strftime("%d-%m-%Y")
        res = self.env['ir.attachment'].sudo().create({
                'name': attname,
                'datas': datas,
                'type': 'binary',
                'store_fname': attname +'.zip',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'mimetype': 'application/zip'
        })
        os.remove(z)
        return res


    template = """
<html>
    <head>
    <link href="https://verificacfdi.facturaelectronica.sat.gob.mx/Content/main.css" rel="stylesheet"><link href="https://verificacfdi.facturaelectronica.sat.gob.mx/Content/satMain.css" rel="stylesheet">
    </head>
    <body class="reduce">
        <div id="cuerpo_principal" class="container top-buffer-submenu reduce">
            <div id="cuerpo" style="margin-top: 25px" class="container  top-buffer-submenu reduce">
        <div id="ctl00_MainContent_UpnlBusqueda">
        <div class="container reduce">
            <div class="row">
            </div>
            <div class="row">
                <img src="data:image/jpeg;base64,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" alt="Logo SHCP" style="height:42px; width:309px;">
            </div>
            <div class="row">
                <h3 class="titulo font-reduce reduce-titulo">Verificaci&oacute;n de comprobantes fiscales digitales por internet</h3><br/>
            </div>
        </div>
        <div id="ctl00_MainContent_PnlResultados">
            <div class="form-group" id="DivContenedor" style="margin-bottom: 0px;">
                <div class="col-sm-12" id="ContenedorDinamico" style="overflow: auto;">
                    <table class="table table-striped" style="margin-bottom: 0px;">
                        <tbody><tr class="headerTable">
                            <th>RFC del emisor </th>
                            <th>Nombre o raz&oacute;n social del emisor </th>
                            <th>RFC del receptor </th>
                            <th>Nombre o raz&oacute;n social del receptor </th>
                        </tr>
                        <tr class="dataTable">
                            <td>
                                <span id="ctl00_MainContent_LblRfcEmisor">{rfcemisor}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblNombreEmisor">{nombreemisor}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblRfcReceptor">{rfcreceptor}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblNombreReceptor">{nombrereceptor}</span>
                            </td>
                        </tr>
                        <tr class="headerTable">
                            <th>Folio fiscal </th>
                            <th>Fecha de expedici&oacute;n </th>
                            <th>Fecha certificaci&oacute;n SAT </th>
                            <th>PAC que certific&oacute; </th>
                        </tr>
                        <tr class="dataTable">
                            <td>
                                <span id="ctl00_MainContent_LblUuid">{uuid}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblFechaEmision">{fechaem}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblFechaCertificacion">{fechatimbre}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblRfcPac">{pac}</span>
                            </td>
                        </tr>
                        <tr class="headerTable">
                            <th>Total del CFDI </th>
                            <th>Efecto del comprobante </th>
                            <th>Estado CFDI </th>
                            <th>Estatus de cancelaci&oacute;n </th>

                        </tr>
                        <tr class="dataTable">
                            <td>
                                <span id="ctl00_MainContent_LblMonto">{total}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblEfectoComprobante">{tipo}</span>
                            </td>
                            <td>
                                <span id="ctl00_MainContent_LblEstado">{vig}</span>
                            </td>
                            <td id="ctl00_MainContent_tdDinamico" >
                                <span id="ctl00_MainContent_LblEsCancelable">{estatus}</span>
                            </td>

                        </tr>
                        <tr class="headerTable">
                            <th id="ctl00_MainContent_thEstatusCancelacion" style="visibility:hidden;">Estatus de cancelaci&oacute;n </th>

                            <th id="ctl00_MainContent_thFechaCancelacion" style="visibility:hidden;">Fecha de Proceso de Cancelaci&oacute;n </th>

                            <th style="visibility: hidden;"></th>
                            <th style="visibility: hidden;"></th>
                        </tr>
                        
                    </tbody></table>
                </div>
            </div>      
        </div>
    </body>
</html>
"""   


        
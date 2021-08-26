import unittest
from select import select

from odoo.tests import TransactionCase, tagged, common
from odoo.exceptions import UserError, AccessError, AccessDenied, Warning, ValidationError

class TestDocumentosPlan(common.TransactionCase):
    def setUp(self):
        super(TestDocumentosPlan, self).setUp()

        self.Users = self.env['res.users'].with_context({'no_reset_password': True})
        self.plananalitico_obj = self.env['das.plananalitico']
        self.asignatura_obj = self.env['das.asignatura']
        self.estadopplan_obj = self.env['das.estadoplan']
        self.docplan_obj = self.env['das.documentosplan']

        self.docente1 = self.Users.create({
            'name': 'Dario Pruebas',
            'login': 'dario_gordillo',
            'email': 'dario.gordillo1993@gmail.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente_consejo').id])]})

        self.docente2 = self.Users.create({
            'name': 'Docente Nuevo',
            'login': 'dario_prueba',
            'email': 'daniale.gl2004@gmail.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente').id])]})

        self.asignatura1 = self.asignatura_obj.create({
            'name': 'Base de datos II',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'user_id': [([], True, [self.docente2])]})

        self.estadoplan1 = self.estadopplan_obj.create({
            'name': 'aprobado'
        })

        self.plananalitico1 = self.plananalitico_obj.create({
            'name': 'Plan xx',
            'fecha_elaboracion': '2021-03-12',
            'version': 1,
            'dependencia_tutoria': 'virtual',
            'asignatura_ids': self.asignatura1.id,
            'estadoplan_id': self.estadoplan1.id
        })


    def test_create_con_docrevisar(self):
        doc_plan1 = self.docplan_obj.create({
            'name': 'Plan Analítico Porgramacion',
            'plananalitico_id': self.plananalitico1.id,
            'documento_revisar': 'aGVsbG8K',
            'documento_aprobado': None,
            'aprobado_consejo': False})
        d = self.docplan_obj.search([('id', '=', doc_plan1.id)], limit=1)
        self.assertEqual(d.documento_revisar, b'aGVsbG8K', 'Documento correcto')
        self.assertTrue(bool(d))

    def test_create_sin_docrevisar(self):
        doc_plan1 = self.docplan_obj.create({
            'name': 'Plan Analítico Porgramacion',
            'plananalitico_id': self.plananalitico1.id,
            'documento_revisar': None,
            'documento_aprobado': None,
            'aprobado_consejo': False})
        d = self.docplan_obj.search([('id', '=', doc_plan1.id)], limit=1)
        self.assertEqual(d.documento_revisar, False, 'Documento correcto')
        self.assertTrue(bool(d))


    def test_write_con_revisor(self):
        doc_plan1 = self.docplan_obj.create({
            'name': 'Plan Analítico Porgramacion',
            'plananalitico_id': self.plananalitico1.id,
            'documento_revisar': 'aGVsbG8K',
            'documento_aprobado': None,
            'aprobado_consejo': False})

        aux = doc_plan1.write({
            'revisor_id': self.docente1.id})
        d = self.docplan_obj.search([('id', '=', doc_plan1.id)], limit=1)
        self.assertTrue(bool(d))
        self.assertEqual(d.revisor_id, self.docente1.id, 'Revisor registrado correctamene')


    def test_write_con_docaprobar(self):
        doc_plan1 = self.docplan_obj.create({
            'name': 'Plan Analítico Porgramacion',
            'plananalitico_id': self.plananalitico1.id,
            'documento_revisar': 'aGVsbG8K',
            'documento_aprobado': None,
            'aprobado_consejo': False,
            'revisor_id': self.docente1.id})

        aux = doc_plan1.write({
            'documento_aprobado': 'Q2hhbwo=',
        })
        d = self.docplan_obj.search([('id', '=', doc_plan1.id)], limit=1)
        self.assertTrue(bool(d))
        self.assertEqual(d.documento_aprobado, b'Q2hhbwo=', 'Documento correcto')

    def test_write_aprobado_consejo(self):
        doc_plan1 = self.docplan_obj.create({
            'name': 'Plan Analítico Porgramacion',
            'plananalitico_id': self.plananalitico1.id,
            'documento_revisar': 'aGVsbG8K',
            'documento_aprobado': None,
            'aprobado_consejo': False,
            'revisor_id': self.docente1.id})

        aux = doc_plan1.write({
            'aprobado_consejo': True,
        })
        d = self.docplan_obj.search([('id', '=', doc_plan1.id)], limit=1)
        self.assertTrue(bool(d))
        self.assertEqual(d.aprobado_consejo, True, 'Documento correcto')




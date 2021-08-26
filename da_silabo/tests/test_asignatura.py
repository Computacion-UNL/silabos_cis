import unittest
from select import select

from odoo.tests import TransactionCase, tagged, common
from odoo.exceptions import UserError, AccessError, AccessDenied, Warning, ValidationError

class TestAsignatura(common.TransactionCase):
    def setUp(self):
        super(TestAsignatura, self).setUp()

        self.Users = self.env['res.users'].with_context({'no_reset_password': True})
        self.asignatura_obj = self.env['das.asignatura']
        self.silabo_obj = self.env['das.silabo']

        self.asignatura10 = self.asignatura_obj.create({
            'name': 'Analisis'})
        self.asignatura11 = self.asignatura_obj.create({
            'name': 'Analisis I'})

    def test_create_sin_docente(self):
        asignatura4 = self.asignatura_obj.create({
            'name': 'Programacion  Web',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'eje_formacion': 'esto es un eje de formacion',
            'tipo': 'obligatorio',
            'credito_totales': 12,
            'credito_teoricos': 12,
            'credito_practicos': 12,
            'n_horas_semanales': 40,
            'n_horas_periodo': 80})
        self.assertTrue(bool(self.asignatura_obj.search([('id', '=', asignatura4.id)], limit=1)))

    def test_create_con_docente(self):
        docente3 = self.Users.create({
            'name': 'Docente Nuevo',
            'login': 'docente1',
            'email': 'd.n@example.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente').id])]})
        asignatura5 = self.asignatura_obj.create({
            'name': 'Programacion Movil',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'user_id': [([],True,[docente3])]})
        self.assertTrue(bool(self.asignatura_obj.search([('id', '=', asignatura5.id)], limit=1)))

    @unittest.skip("Materia repetida")
    def test_create_materia_repetida(self):
        docente1 = self.Users.create({
            'name': 'Raul Perez',
            'login': 'raul1',
            'email': 'r.p@example.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente').id])]})
        self.asignatura6 = self.asignatura_obj.create({
            'name': 'Programacion II',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'eje_formacion': 'esto es un eje de formacion',
            'tipo': 'obligatorio',
            'credito_totales': 12,
            'credito_teoricos': 12,
            'credito_practicos': 12,
            'n_horas_semanales': 40,
            'n_horas_periodo': 80,
            'user_id': [([],True,[docente1])]})

        asignatura7 = self.asignatura_obj.create({
            'name': 'Programacion II',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'eje_formacion': 'esto es un eje de formacion',
            'tipo': 'obligatorio',
            'credito_totales': 12,
            'credito_teoricos': 12,
            'credito_practicos': 12,
            'n_horas_semanales': 40,
            'n_horas_periodo': 80,
            'user_id': [([], True, [docente1])]})
        self.assertFalse(bool(self.asignatura_obj.search([('id', '=', asignatura7.id)], limit=1)))

    def test_write_sin_docente(self):
        docente4 = self.Users.create({
            'name': 'Docente Nuevo2',
            'login': 'docente2',
            'email': 'd2.n@example.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente').id])]})

        asignatura8 = self.asignatura_obj.create({
            'name': 'Base de datos',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03',
            'user_id': [([], True, [docente4])]})
        aux = self.asignatura_obj.write({
            'user_id': [([],False,[])]})
        self.assertTrue(asignatura8.user_id != None)

    def test_write_con_docente(self):
        docente4 = self.Users.create({
            'name': 'Docente Nuevo2',
            'login': 'docente2',
            'email': 'd2.n@example.com',
            'notification_type': 'email',
            'groups_id': [(6, 0, [self.env.ref('da_silabo.res_groups_docente').id])]})

        self.asignatura9 = self.asignatura_obj.create({
            'name': 'Base de datos',
            'codigo_institucional': 'b13',
            'codigo_unesco': 'u03'})
        aux = self.asignatura_obj.write({
            'user_id': [([self.asignatura9.id],True,[docente4])]})

        self.assertTrue(self.asignatura9.user_id != None)

    @unittest.skip("Materia repetida")
    def test_write_materia_repetida(self):
        self.asignatura11.write({
            'name': 'Analisis'})

        nombre_asignatura1 = self.asignatura10.name
        print(nombre_asignatura1)
        nombre_asignatura = self.asignatura11.name
        print(nombre_asignatura)

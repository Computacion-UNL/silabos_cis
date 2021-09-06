from _ast import expr
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pip._vendor.six import print_

from odoo import fields, models, api, SUPERUSER_ID
from odoo.exceptions import ValidationError
from pyparsing import empty
import logging
_logger = logging.getLogger(__name__)

class ResUser(models.Model):
    _inherit = "res.users"
    es_administrador = fields.Boolean(string='Es Administrador', store=True)

    #perfil_id = fields.One2many("das.perfil", "user_id", ondelete="cascade")


class Perfil(models.Model):
    _name = "das.perfil"
    _description = "Perfil academido del docente"

    titulo_tn = fields.Html(string='Titulo de tercer nivel')
    titulo_cn = fields.Html(string='Titulo de cuarto nivel')
    habilidades = fields.Html(string='Habilidades del Docente')
    actitudes = fields.Html(string='Actitudes del Docente')

    silabo_id = fields.Many2one("das.silabo", string="Docente",
                                        default=lambda self: self.env['das.silabo'].search([], limit=1),
                                        ondelete="cascade")


class Asignatura(models.Model):

    _name = "das.asignatura"
    _description = "Asignaturas"

    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El nombre de la Asignatura ya existe!"),
    ]

    name = fields.Char(string="Nombre de la asignatura", required=True)
    codigo_institucional = fields.Char(string="Código institucional")
    codigo_unesco = fields.Char(string="Código unesco")
    eje_formacion = fields.Char(string="Eje de Formación")
    tipo = fields.Selection(selection=[("obligatorio", "Obligatorio"), ("comple", "Complementario"),
                                       ("optativa", "Optativa"), ("otra", "Otra")],
                               string="Tipo",
                               default="obligatorio")
    credito_totales = fields.Integer(string="Créditos Totales")
    credito_teoricos = fields.Integer(string="Créditos Teóricos")
    credito_practicos = fields.Integer(string="Créditos Prácticos")
    n_horas_semanales = fields.Integer(string="Horas Semanales")
    n_horas_periodo = fields.Integer(string="Horas Periodo")
    fecha_asignacion = fields.Date(string="Fecha de Asignacion")
    fecha_culminacion = fields.Date(string="Fecha de Entrega del Sílabo")

    
    prerrequisitos = fields.Many2many("das.asignatura", "das_asignatura_pre_rel",
                                      "asignatura_id", "asignaturac_id", string="Prerrequisitos")
    #prerrequisitos = fields.One2many("das.asignatura", "prerrequisitos_ids",string="Prerrequisitos de la Asignatura")
    #prerrequisitos_ids = fields.Many2one(
    #    "das.asignatura", string="Asignatura",
     #   default=lambda self: self.env['das.asignatura'].search([], limit=1),
      #  ondelete="cascade")
    correquisitos = fields.Many2many("das.asignatura", "das_asignatura_co_rel",
                                     "asignatura_id", "asignaturac_id", string="Correquisitos")

    user_id = fields.Many2many(
        'res.users', 'das_user_rel_user',
        'user_id', 'asignatura_id', string='Docentes')

    silabo_ids = fields.Many2many(
        'das.silabo', 'das_silabo_rel',
        'silabo_id', 'asignatura_id', string='Silabo'
    )



    @api.onchange('user_id', 'fecha_culminacion')
    def _asignarFechaAsignacion(self):
        hoy = fields.Date.today()
        aux = fields.Datetime.from_string(hoy) + relativedelta(days=4)
        print(hoy)
        print(aux)
        print(self.fecha_culminacion)
        if self.fecha_culminacion != False:
            if fields.Datetime.from_string(self.fecha_culminacion) >= aux:
                self.fecha_asignacion = hoy
                #self.fecha_culminacion = fecha_culmina
                print(self.fecha_asignacion)
                print(self.fecha_culminacion)
            else:
                self.fecha_culminacion = aux
                raise ValidationError("La fecha de entrega del Sílabo debe tener un mínimo de 4 días después de la asignación"
                                  " para su entrega!!")

    @api.onchange('correquisitos')
    def _modificarCorrequisitos(self):
        for c in self.correquisitos:
            if c._origin.id == self._origin.id:
                raise ValidationError("No se puede asignar la misma materia como Correquisito!!")

    @api.model
    def create(self, vals):
        """
            Sobrecarga del método create de la clase Asignatura para controlar la
            creación de un solo registro activo vigente, además de validar que
            la fecha de finalización del Plan sea mayor a la fecha actual y la
            fecha inicio del Plan menor a la fecha de finalización.
            :param vals: Campos del modelo, como una lista de diccionarios.
            :returns: La creación de un nuevo Plan.
        """
        usuario = vals.get('user_id')
        nombre_asignatura = vals.get('name')
        if usuario != None and usuario !=False:
            if bool(usuario[0][2]) == True:
                self.notificarAsignacionAsignatura(usuario, nombre_asignatura)
            else:
                self.env.user.notify_info(
                    message='No existen usuarios vinculados a la asignatura')
        return super(Asignatura, self).create(vals)


    def write(self, vals):
        """Override default Odoo write function and extend."""
        usuario = vals.get('user_id')


        nombre_asignatura = vals.get('name')
        if nombre_asignatura == None or nombre_asignatura == False:
            nombre_asignatura = self.name
        if usuario != None and bool(usuario[0][2]) == True:
            self.cambioPlanSilabo(usuario[0][2], self.user_id, self.id)
            print("Borrar #, se va a notificar")
            self.notificarAsignacionAsignatura(usuario, nombre_asignatura)
        elif self.env.user.has_group('da_silabo.res_groups_administrador'):
            self.env.user.notify_info(
                message='No existen usuarios vinculados a la asignatura')
        return super(Asignatura, self).write(vals)


    def cambioPlanSilabo(self, docentes_nuevos, docentes_viejos, asignatura_id):

        if len(docentes_nuevos) == len(docentes_viejos):
            for i in range(len(docentes_nuevos)):
                docente = self.env["res.users"].search([('id', '=', docentes_nuevos[i])])
                plan = self.env["das.plananalitico"].search([('responsable', '=', docentes_viejos[i].id),('asignatura_ids', '=', asignatura_id)])
                if plan and docente:
                    plan.write({"responsable": docente})

                silabo = self.env["das.silabo"].search([('responsable', '=', docentes_viejos[i].id),('asignatura_ids', '=', asignatura_id)])
                if silabo and docente:
                    silabo.write({"responsable": docente})
        elif len(docentes_nuevos) <= 2 and len(docentes_nuevos) > 0  and len(docentes_viejos) <=2 and len(docentes_viejos) > 0:
            docente = self.env["res.users"].search([('id', '=', docentes_nuevos[0])])
            plan = self.env["das.plananalitico"].search(
                [('responsable', '=', docentes_viejos[0].id), ('asignatura_ids', '=', asignatura_id)])
            if plan and docente:
                plan.write({"responsable": docente})

            silabo = self.env["das.silabo"].search(
                [('responsable', '=', docentes_viejos[0].id), ('asignatura_ids', '=', asignatura_id)])
            if silabo and docente:
                silabo.write({"responsable": docente})

        self.env.cr.commit()

        #if len(docentes_nuevos) < len(docentes_viejos):








    def notificarAsignacionAsignatura(self, usuario, nombre_asignatura):
        asunto = "Asignación del sílabo para la asignatura %s" % nombre_asignatura
        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            for u in usuario[0][2]:
                if u == us.id and us.has_group('da_silabo.res_groups_docente'):
                    try:
                        template_rec = self.env.ref('da_silabo.email_template_asignacion_asignatura')
                        template_rec.write({'email_to': us.email})
                        template_rec.write({'subject': asunto})
                        template_rec.send_mail(us.id, force_send=True)
                    except:
                        raise ValidationError("Se produjo un error al envío de notificación.")


    def notificacion_silabo(self):
        """
            Método ejecutado con acción planificada 'cron', para notificar mediante correo electrónico a los
            usuarios sobre la expiración de una Tarea en específico y cambio del estado de la tarea.
        """

        today = fields.Datetime.today()

        lista_asignaturas = self.env["das.asignatura"].search([])
        print(lista_asignaturas)
        for a in lista_asignaturas:
            print(a.name)
            print(today)
            fecha_c = fields.Datetime.from_string(a.fecha_culminacion)
            print(fields.Datetime.from_string(a.fecha_culminacion))

            print(a.user_id)
            print(bool(a.user_id))
            silabo_aceptado = self.env["das.silabo"].search([('asignatura_ids', '=', a.id),('fecha_aprobacion','!=',False)])
            print(bool(silabo_aceptado))
            if fecha_c and bool(silabo_aceptado) == False:
                if bool(a.user_id) and today < fecha_c:
                    asunto = "Notificación elaboración del Sílabo - %s" % a.name
                    for us in a.user_id:
                        print(us.name)
                        if us.has_group('da_silabo.res_groups_docente'):
                            try:
                                template_rec = self.env.ref('da_silabo.email_template_notificacion_silabo')
                                template_rec.write({'email_from': us.company_id.email})
                                template_rec.write({'email_to': us.email})
                                template_rec.write({'subject': asunto})
                                template_rec.send_mail(a.id, force_send=True)
                            except:
                                print("Norificacion silabo cron")
                                pass


class TipoAprendizaje(models.Model):
    _name = "das.tipoaprendizaje"
    _description = "Tipo de Aprendizaje"
    _order = 'sequence'

    name = fields.Char(string="Nombre", required=True)
    description = fields.Char(string="Descripción")
    sequence = fields.Integer()

    _sql_constraints = [
        ('name_unique', 'unique (name)',
         "El Nombre del tipo de aprendizaje ya existe!"),
    ]


class Ciclo(models.Model):
     _name = "das.ciclo"
     _description = "Ciclo y Paralelo"

     name = fields.Selection(selection=[("ciclo_1","Primer Ciclo"), ("ciclo_2","Segundo Ciclo"), ("ciclo_3","Tercer Ciclo"),
                                        ("ciclo_4", "Cuarto Ciclo"), ("ciclo_5","Quinto Ciclo"), ("ciclo_6","Sexto Ciclo"),
                                        ("ciclo_7","Séptimo Ciclo"), ("ciclo_8","Octavo Ciclo"), ("ciclo_9","Noveno Ciclo"),
                                        ("ciclo_10","Décimo Ciclo")], string="Ciclo", default ="ciclo_1")
     paralelo = fields.Selection(selection=[("paralelo_a","A"), ("paralelo_b","B"), ("paralelo_c","C")], string="Paralelo", default = "paralelo_a")

     periodoacademico_ids = fields.Many2one(
        "das.periodoacademico", string = "Periodo Académico",
        default=lambda self: self.env['das.periodoacademico'].search([], limit=1),
        ondelete="cascade")

     asignatura_ids = fields.Many2many(
         'das.asignatura', 'das_asignatura_rel',
         'asignatura_id', 'ciclo_id', string='Asignaturas'
     )

class PeriodoAcademico(models.Model):
     _name = "das.periodoacademico"
     _description = "Período Académico"

     name = fields.Char(string="Nombre", required=True)
     fecha_inicio = fields.Date(string="Fecha de Inicio", required = True)
     fecha_fin = fields.Date(string="Fecha de Finalización", required = True)




class ProgramaEstudios(models.Model):
    _name = "das.programaestudios"
    _description = "Programa de Estudios"

    name = fields.Char(string="Nombre", required=True)
    nivel = fields.Selection(selection=[("pregrado", "Pregrado"),
                                           ("postgrado", "Postgrado")],
                                string="Nivel", required=True)
    vigencia = fields.Selection(selection=[("si", "SI"),
                                       ("no", "NO")],
                            string="Vigencia", required=True)
    lugar = fields.Char(string="Lugar", required=True)
    ute = fields.Selection(selection=[("si", "SI"),
                                           ("no", "NO")],
                                string="Titulación (UTE o Complexivo)", required=True)

    ciclo_ids = fields.Many2many(
        'das.ciclo', 'das_ciclo_rel',
        'ciclo_id', 'programaestudios_id', string='Ciclos'
    )


class DocumentosPlan(models.Model):
    _name = "das.documentosplan"
    _description = "Documentos del Plan Analítico"
    _inherit = "mail.thread"

    name = fields.Char(compute="_asignarNombre")

    plananalitico_id = fields.Many2one("das.plananalitico", string="Plan Analítico", required=True,
                                     default=lambda self: self.env['das.plananalitico'].search([], limit=1))
    documento_revisar = fields.Binary(string="Cargue el documento firmado a ser revisado")
    documento_aprobado = fields.Binary(string="Cargue el documento firmado y aprobado")

    aprobado_consejo = fields.Boolean(default=False, string="Plan Analítico Revisado?")

    revisor_id = fields.Many2one("res.users", string="Revisor")


    @api.depends('name','plananalitico_id')
    def _asignarNombre(self):
        print(self.plananalitico_id.name)
        print(self.plananalitico_id)
        self.name = self.plananalitico_id.name

    @api.model
    def create(self, vals):
        """
            Sobrecarga del método create de la clase Asignatura para controlar la
            creación de un solo registro activo vigente, además de validar que
            la fecha de finalización del Plan sea mayor a la fecha actual y la
            fecha inicio del Plan menor a la fecha de finalización.
            :param vals: Campos del modelo, como una lista de diccionarios.
            :returns: La creación de un nuevo Plan.
        """
        doc_revisar = vals.get('documento_revisar')
        doc_aprobado = vals.get('documento_aprobado')
        plananalitico = vals.get('plananalitico_id')
        
        print(doc_revisar)
        print(doc_aprobado)
        print(plananalitico)
        if doc_revisar != False and doc_revisar != None:
            print("Create revision")
            self._notificar_revision_create(plananalitico)

        if doc_aprobado != False and doc_aprobado != None:
            print("Create aprobacion")
            self._notificar_aprobacion_create(plananalitico)
        return super(DocumentosPlan, self).create(vals)


    def write(self, vals):
        """Override default Odoo write function and extend."""
        doc_revisar = vals.get('documento_revisar')
        doc_aprobado = vals.get('documento_aprobado')
        plananalitico = vals.get('plananalitico_id')
        apro_consejo = vals.get('aprobado_consejo')
        revisor = vals.get('revisor_id')
        print(doc_revisar)
        print(doc_aprobado)
        print(apro_consejo)
        print(plananalitico)

        if plananalitico == None or plananalitico == False:
            print("Entra")
            print(plananalitico)
            plananalitico = self.plananalitico_id
            print(plananalitico)


        if doc_revisar != None and doc_revisar != False:
            print(doc_revisar)
            print(self.documento_revisar != doc_revisar)
            print("Write revision")
            self._notificar_revision(plananalitico)

        if doc_aprobado != None and doc_aprobado != False:
            print("Write aprobacion")
            self._notificar_aprobacion(plananalitico)
            aux = datetime.now().strftime("%Y-%m-%d")
            self.env["das.plananalitico"].browse(plananalitico.id).write({"fecha_aprobacion": aux})
            self.env.cr.commit()

        if apro_consejo != None and apro_consejo != False:
            print("Entra revisor chek")
            self._notificar_revision_consejo(plananalitico)

        if revisor != None and revisor != False:
            print("Entra notificar revisor")
            self._notificar_revisor(plananalitico, revisor)

        return super(DocumentosPlan, self).write(vals)

    def _notificar_revision(self, plananalitico):
        """
            Notifica al gestor cuando el Plan analítico esta para su revision.
        """
        plan = self.env["das.plananalitico"].search([('id', '=', plananalitico.id)], limit=1)
        asunto = "Revisión del Plan Analítico denominado: %s" % plan.name

        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_plan_revisar')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revision_create(self, plananalitico):
        """
            Notifica al gestor cuando el Plan analítico esta para su revision.
        """
        plan = self.env["das.plananalitico"].search([('id', '=', plananalitico)], limit=1)
        print(plan.id)
        print(plan.name)
        asunto = "Revisión del Plan Analítico denominado: %s" % plan.name

        usuarios = self.env["res.users"].search([])
        print(usuarios)

        for us in usuarios:
            print(us.name)
            print(us.email)
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_plan_revisar')
                    print("llega")
                    template_rec.write({'email_to': us.email})
                    print("llega")
                    template_rec.write({'subject': asunto})
                    print("llega")
                    template_rec.send_mail(us.id, force_send=True)
                    print("llega")
                    break
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_aprobacion(self, plananalitico):
        """
            Notifica al docente cuando el Plan analítico tenga una fecha de aprobación.
        """
        plan = self.env["das.plananalitico"].search([('id', '=', plananalitico.id)], limit=1)
        print(plan.name)
        print(plan)
        asunto = "Aprobación del : %s" % plan.name

        usuarios = plan.asignatura_ids.user_id

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_docente'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_plan_aprobado')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_aprobacion_create(self, plananalitico):
        """
            Notifica al docente cuando el Plan analítico tenga una fecha de aprobación.
        """
        plan = self.env["das.plananalitico"].search([('id', '=', plananalitico)], limit=1)
        print(plan.name)
        print(plan)
        asunto = "Aprobación del : %s" % plan.name

        usuarios = plan.asignatura_ids.user_id

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_docente'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_plan_aprobado')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revision_consejo(self, plananalitico):
        """
            Notifica al gestor cuando el Plan analítico ha sido revisado por el consejo.
        """
        print(plananalitico)

        plan = self.env["das.plananalitico"].search([('id', '=', int(plananalitico.id))], limit=1)

        asunto = "Revisión del Consejo Consultivo del Plan Analítico denominado: %s" % plan.name

        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_plan_revisar_consejo')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revisor(self, plananalitico, rev_id):
        """
            Notifica al gestor cuando el Plan analítico esta para su revision.
        """
        print(plananalitico)
        plan = self.env["das.plananalitico"].search([('id', '=', plananalitico.id)], limit=1)
        asunto = "Revisión del Consejo Consultivo del Plan Analítico denominado: %s" % plan.name

        us = self.env["res.users"].search([('id', '=', rev_id)], limit=1)

        if us.has_group('da_silabo.res_groups_docente_consejo'):
            try:
                template_rec = self.env.ref('da_silabo.email_template_asignacion_revisor_plan')
                template_rec.write({'email_to': us.email})
                template_rec.write({'subject': asunto})
                template_rec.send_mail(us.id, force_send=True)
            except:
                raise ValidationError("Se produjo un error al envío de notificación.")

    def send_mail_template(self):
        print("ENtro")
        rev_id = self.revisor_id
        plananalitico = self.plananalitico_id
        self._notificar_revisor(plananalitico, rev_id.id)

class PlanAnalitico(models.Model):
     _name = "das.plananalitico"
     _description = "Plan Analítico"
     _inherit = "mail.thread"

     name = fields.Char(string="Nombre del Plan Análitico", default="Plan Analítico")
     responsable = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user)
     fecha_elaboracion = fields.Date(string="Fecha de Elaboración", required=True, default=fields.Date.today())
     fecha_aprobacion = fields.Date(string="Fecha de Aprobación")
     metodologia = fields.Text(string="Metodología de la Asignatura")
     version = fields.Integer(string="Versión", required=True, default = 1)
     dependencia_tutoria = fields.Selection(selection=[("virtual", "Virtual"),
                                         ("presencial", "Presencial")], default = 'presencial',
                              string="Dependencia para Tutorías", required=True)
     contrib_formacion_profesional = fields.Text(
         string="Contribución de la asignatura a la formación profesional")
     objetivos = fields.Text(string="Objetivos")

     estrategia_metodologicas = fields.Text(string="Estrategias Metodológicas")
     resultados_aprendizaje = fields.Text(string="Resultados de Aprendizaje")


     asignatura_ids = fields.Many2one("das.asignatura", string="Asignatura", required=True,
                                 default=lambda self: self.env['das.asignatura'].search([], limit=1),
                                 group_expand='_group_expand_stage_ids')


     bibliografia_ids = fields.Many2many(
         'das.bibliografia', 'das_biblio_rel',
         'bibliografia_id', 'planalitico_id', string='Bibliografia'
     )

     criterioevaluacion_id = fields.One2many("das.criteriosevaluacion", "plananalitico_id",
                                             string="Criterios de Evaluacion",
                                             ondelete="cascade")

     contenidoplan_id = fields.One2many("das.contenidosplan", "plananalitico_id",
                                             string="Contenido del Plan Analítico",
                                             ondelete="cascade")

     state = fields.Selection([("inicio", "Borrador"),("fin", "Finalizado")], default="inicio",  string="Status")

     @api.model
     def _group_expand_stage_ids(self, stages, domain, order):
         """ Read group customization in order to display all the stages in the
             kanban view, even if they are empty
         """
         stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
         return stages.browse(stage_ids)
     
     @api.model
     def create(self, vals):
         asignatura = vals.get('asignatura_ids')
         plan = self.env["das.plananalitico"].search([('asignatura_ids', '=', asignatura)])
         if plan:
             raise ValidationError ("Ya existe un Plan Analítico para esa asignatura!")

         return super(PlanAnalitico, self).create(vals)

     def action_confirm(self):
         aux = 'Datos Incompletos'
         aux2 = False
         #self.env.user.notify_info(message=bool(self.asignatura_ids))
         #self.env.user.notify_info(message=bool(self.bibliografia_ids))
         # if self.bibliografia_ids == None and self.criterioevaluacion_id == None:
         # if bool(self.metodologia) != False:
         #   self.env.user.notify_info(message=aux)
         # if self.bibliografia_ids == None:
         # else:
         #    self.state = 'fin'
         # a = self.env.user.notify_info(message=aux)
         # else:
         #   self.state = 'fin'

         #self.env.user.notify_info(self.metodologia)

         _logger.error(type(self.metodologia))
         _logger.error(bool(self.metodologia))

         if bool(self.metodologia) == False:
             aux2 = True
         if bool(self.name) == False:
             aux2 = True
         if bool(self.bibliografia_ids) == False:
             aux2 = True
         if bool(self.contenidoplan_id) == False:
             aux2 = True
         if bool(self.criterioevaluacion_id) == False:
             aux2 = True
         if bool(self.resultados_aprendizaje) == False:
             aux2 = True
         if bool(self.estrategia_metodologicas) == False:
             aux2 = True
         if bool(self.contrib_formacion_profesional) == False:
             aux2 = True
         if bool(self.objetivos) == False:
             aux2 = True

         if aux2:
             #self.env.user.notify_info(message='Entra IF')
             self.env.user.notify_info(message=aux)
             # self.env.user.notify_info(message=bool(self.metodologia))

         else:
             self.state = 'fin'
             #self.env.user.notify_info(message='Entra Else')

     def action_return(self):
         for rec in self:
             rec.state = 'inicio'

class ContenidosPlan(models.Model):
     _name = "das.contenidosplan"
     _description ="Contenidos Mínimos de la Asignatura"

     numero = fields.Integer(string="Número de Orden", required=True)
     nombre_unidad = fields.Char(string="Número y orden de la Unidad", required=True)
     detalle_contenidos = fields.Html(string="Detalle de Contenidos", required = True)
     horas_profesor= fields.Integer(string="Número de horas para el aprendizaje asistido por el profesor", required = True)
     horas_tutorias = fields.Integer(string="Número de horas para el aprendizaje colaborativo(tutorías)", required = True)
     horas_practicas = fields.Integer(string="Número de horas para prácticas de aplicación y experimentación de aprendizajes", required = True)
     horas_autonomo = fields.Integer(string="Número de horas para el aprendizaje autónomo", required = True)

     plananalitico_id = fields.Many2one("das.plananalitico", string="Plan Analitico",
                                        default=lambda self: self.env['das.plananalitico'].search([], limit=1),
                                        group_expand='_group_expand_stage_ids',
                                        ondelete="cascade")


class DocumentosSilabo(models.Model):
    _name = "das.documentossilabo"
    _description = "Documentos del Sílabo"
    _inherit = "mail.thread"

    name = fields.Char(compute="_asignarNombre")

    silabo_id = fields.Many2one("das.silabo", string="Sílabo", required=True,
                                     default=lambda self: self.env['das.silabo'].search([], limit=1))
    documento_revisar = fields.Binary(string="Cargue el documento firmado a ser revisado")
    documento_aprobado = fields.Binary(string="Cargue el documento firmado y aprobado")

    aprobado_consejo = fields.Boolean(default=False, string="Sílabo Revisado?")

    revisor_id = fields.Many2one("res.users", string="Revisor")

    expirado = fields.Selection(selection=[("no_expired", "No Expirado"), ("expired", "Expirado")],
                                string="Tiempo Límite",
                                default="no_expired")

    def check_expiry_silabo(self):
        """
                    Método ejecutado con acción planificada 'cron', para notificar mediante correo electrónico a los
                    usuarios sobre la expiración de una Tarea en específico y cambio del estado de la tarea.
                """

        today = fields.Date.today()
        documentos = self.env["das.documentossilabo"].search([])
        for documento in documentos:
            fecha_culminacion = documento.silabo_id.asignatura_ids.fecha_culminacion
            print("ENtra")
            print(fecha_culminacion)
            print(today)
            if documento.expirado == "no_expired" and fecha_culminacion < today:

                documento.expirado = "expired"
                if (documento.silabo_id.responsable.has_group('da_silabo.res_groups_docente')) and (documento.documento_revisar != None
                                                                                                    or documento.documento_revisar != False):
                    asunto = "Notificación de expiración del Sílabo - %s" % documento.silabo_id.name
                    try:
                        template_rec = self.env.ref('da_silabo.email_template_notificacion_silabo_expirado')
                        template_rec.write({'email_from': documento.silabo_id.responsable.company_id.email})
                        template_rec.write({'email_to': documento.silabo_id.responsable.email})
                        template_rec.write({'subject': asunto})
                        template_rec.send_mail(documento.silabo_id.id, force_send=True)
                    except:
                        pass


    @api.depends('name', 'silabo_id')
    def _asignarNombre(self):
        print(self.silabo_id.name)
        print(self.silabo_id)
        self.name = self.silabo_id.name


    #Documento Sílabo funciones
    @api.model
    def create(self, vals):
        """
            Sobrecarga del método create de la clase Asignatura para controlar la
            creación de un solo registro activo vigente, además de validar que
            la fecha de finalización del Plan sea mayor a la fecha actual y la
            fecha inicio del Plan menor a la fecha de finalización.
            :param vals: Campos del modelo, como una lista de diccionarios.
            :returns: La creación de un nuevo Plan.
        """
        doc_revisar = vals.get('documento_revisar')
        doc_aprobado = vals.get('documento_aprobado')
        silabo = vals.get('silabo_id')
        print(doc_revisar)
        print(doc_aprobado)
        if doc_revisar != False and doc_revisar != None:
            print("Create revision")
            self._notificar_revision_create(silabo)

        if doc_aprobado != False and doc_aprobado != None:
            print("Create aprobacion")
            self._notificar_aprobacion_create(silabo)
        return super(DocumentosSilabo, self).create(vals)

    def write(self, vals):
        """Override default Odoo write function and extend."""
        doc_revisar = vals.get('documento_revisar')
        doc_aprobado = vals.get('documento_aprobado')
        silabo = vals.get('silabo_id')
        apro_consejo = vals.get('aprobado_consejo')
        revisor = vals.get('revisor_id')
        print(doc_revisar)
        print(doc_aprobado)
        print(apro_consejo)
        print(silabo)

        if silabo == None or silabo == False:
            print("Entra")
            print(silabo)
            silabo = self.silabo_id

        if doc_revisar != None and doc_revisar != False:
            print(doc_revisar)
            print(self.documento_revisar != doc_revisar)
            print("Write revision")
            self._notificar_revision(silabo)

        if doc_aprobado != None and doc_aprobado != False:
            print("Write aprobacion")
            self._notificar_aprobacion(silabo)
            aux = datetime.now().strftime("%Y-%m-%d")
            self.env["das.silabo"].browse(silabo.id).write({"fecha_aprobacion": aux})
            self.env.cr.commit()

        if apro_consejo != None and apro_consejo != False:
            print("Entra revisor chek")
            self._notificar_revision_consejo(silabo)

        if revisor != None and revisor != False:
            print("Entra notificar revisor")
            self._notificar_revisor(silabo, revisor)

        return super(DocumentosSilabo, self).write(vals)

    def _notificar_revision(self, silabo):
        """
            Notifica al gestor cuando el Sílabo esta para su revision.
        """
        silab = self.env["das.silabo"].search([('id', '=', silabo.id)], limit=1)
        asunto = "Revisión del Sílabo denominado: %s" % silab.name

        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_silabo_revisar')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revision_create(self, silabo):
        """
            Notifica al gestor cuando el Sílabo esta para su revision.
        """
        silab = self.env["das.silabo"].search([('id', '=', silabo)], limit=1)
        asunto = "Revisión del Sílabo denominado: %s" % silab.name

        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_silabo_revisar')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_aprobacion(self, silabo):
        """
            Notifica al docente cuando el Sílabo tenga una fecha de aprobación.
        """
        silab = self.env["das.silabo"].search([('id', '=', silabo.id)], limit=1)
        print(silab.name)
        print(silab)
        asunto = "Aprobación del : %s" % silab.name

        usuarios = silab.asignatura_ids.user_id

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_docente'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_silabo_aprobado')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_aprobacion_create(self, silabo):
        """
            Notifica al docente cuando el Sílabo tenga una fecha de aprobación.
        """
        silab = self.env["das.silabo"].search([('id', '=', silabo)], limit=1)
        print(silab.name)
        print(silab)
        asunto = "Aprobación del : %s" % silab.name

        usuarios = silab.asignatura_ids.user_id

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_docente'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_silabo_aprobado')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revision_consejo(self, silabo):
        """
            Notifica al gestor cuando el Sílabo esta para su revision.
            int(plananalitico.id))
        """
        silab = self.env["das.silabo"].search([('id', '=', int(silabo.id))], limit=1)
        asunto = "Revisión del Consejo Consultivo del Sílabo: %s" % silab.name

        usuarios = self.env["res.users"].search([])

        for us in usuarios:
            if us.has_group('da_silabo.res_groups_administrador'):
                try:
                    template_rec = self.env.ref('da_silabo.email_template_silabo_revisar_consejo')
                    template_rec.write({'email_to': us.email})
                    template_rec.write({'subject': asunto})
                    template_rec.send_mail(us.id, force_send=True)
                except:
                    raise ValidationError("Se produjo un error al envío de notificación.")

    def _notificar_revisor(self, silabo, rev_id):
        """
            Notifica al gestor cuando el Sílabo esta para su revision.
        """
        print(silabo)
        silab = self.env["das.silabo"].search([('id', '=', silabo.id)], limit=1)
        asunto = "Revisión del Consejo Consultivo del Sĺlabo denominado: %s" % silab.name

        us = self.env["res.users"].search([('id', '=', rev_id)], limit=1)

        if us.has_group('da_silabo.res_groups_docente_consejo'):
            try:
                template_rec = self.env.ref('da_silabo.email_template_asignacion_revisor_silabos')
                template_rec.write({'email_to': us.email})
                template_rec.write({'subject': asunto})
                template_rec.send_mail(us.id, force_send=True)
            except:
                raise ValidationError("Se produjo un error al envío de notificación.")

    def send_mail_template(self):
        print("ENtro")
        rev_id = self.revisor_id
        silabo = self.silabo_id
        self._notificar_revisor(silabo, rev_id.id)



class Silabo(models.Model):
     _name = "das.silabo"
     _description = "Sílabo"
     _inherit = "mail.thread"

     name = fields.Char(string="Nombre del Sílabo", default="Sílabo de ")
     valores = fields.Html(string="Actitudes y valores")
     recursos = fields.Html(string="Recursos/Materiales didácticos")
     horario = fields.Html(string="Horario de clases")
     fecha_elaboracion = fields.Date(string="Fecha de elaboración del sílabo", required = True, default=fields.Date.today())
     fecha_revision = fields.Date(string="Fecha de revisión del Sílabo")
     fecha_aprobacion = fields.Date(string="Fecha de aprobación del Sílabo")
     fecha_actualizacion = fields.Date(string="Fecha de actualización del Sílabo")
     responsable = fields.Many2one("res.users", string="Responsable", default=lambda self: self.env.user)
     version = fields.Integer(string="Versión")
     plananalitico_id = fields.Many2one("das.plananalitico", string="Plan Analitico",
                                     required=True,
                                     ondelete="cascade")

     unidad_ids = fields.One2many("das.unidad", "silabo_id")

     sesion_ids = fields.One2many("das.sesion", "silabo_id")

     tipoaprendizaje_ids = fields.Many2many(
         'das.tipoaprendizaje', 'das_tipoaprendizaje2_rel',
         'tipoaprendizaje_id', 'silabo_id', string='Tipo de Aprendizaje')


     bibliografia_ids = fields.Many2many(
         'das.bibliografia', 'das_biblio2_rel',
         'bibliografia_id', 'silabo_id', string='Bibliografia'
     )

     revisor_id = fields.Many2one("res.users", string="Revisor")


     perfil_ids = fields.One2many("das.perfil", "silabo_id", ondelete="cascade")

     asignatura_ids = fields.Many2one("das.asignatura", string="Asignatura", required=True,
                                      default=lambda self: self.env['das.asignatura'].search([], limit=1),
                                      group_expand='_group_expand_stage_ids')



     contribucion_ids = fields.One2many("das.contribucion", "silabo_id")

     perfilegreso_ids = fields.One2many("das.perfilegreso", "silabo_id")

     state = fields.Selection([("inicio", "Borrador"), ("fin", "Finalizado")], default="inicio", string="Status")


     def action_confirm(self):
         aux = 'Datos incompletos'
         aux2 = False

         if bool(self.name)==False:
             aux2 = True
         if bool(self.unidad_ids)==False:
             aux2 = True
         if bool(self.sesion_ids)==False:
             aux2 = True
         if bool(self.tipoaprendizaje_ids)==False:
             aux2 = True
         if bool(self.bibliografia_ids)==False:
             aux2 = True
         if bool(self.perfil_ids)==False:
             aux2 = True
         if bool(self.contribucion_ids)==False:
             aux2 = True
         if bool(self.perfilegreso_ids)==False:
             aux2 = True

         if aux2:
             self.env.user.notify_info(message=aux)
         else:
             self.state = 'fin'

     def action_return(self):
         for rec in self:
             rec.state = 'inicio'

     @api.model
     def _group_expand_stage_ids(self, stages, domain, order):
        """ Read group customization in order to display all the stages in the
            kanban view, even if they are empty
        """
        stage_ids = stages._search([], order=order, access_rights_uid=SUPERUSER_ID)
        return stages.browse(stage_ids)
     @api.onchange('plananalitico_id')
     def _validarPlanconAsignatura(self):
         print("ENtra")
         print(self.id)
         if bool(self.plananalitico_id) != False:
            if self.asignatura_ids != self.plananalitico_id.asignatura_ids:
                raise ValidationError("El Plan Analítico seleccionado es distinto a la Asignatura")
     @api.model
     def create(self, vals):
         asignatura = vals.get('asignatura_ids')
         silabo = self.env["das.silabo"].search([('asignatura_ids', '=', asignatura)])
         if silabo:
             raise ValidationError("Ya existe un Sílabo para esa asignatura!")

         return super(Silabo, self).create(vals)


class CriteriosEvaluacion(models.Model):
     _name = "das.criteriosevaluacion"
     _description = "Criterios de Evaluación"

     parametros_evaluacion = fields.Html(string="Parámetros de Evaluación")
     evaluacion1 = fields.Float(string="Puntaje primera evaluación", required = True)
     evaluacion2 = fields.Float(string="Puntaje segunda evaluación",required=True)
     evaluacion3 = fields.Float(string="Puntaje tercera evaluación", required = True)
     puntaje_total = fields.Float(string="Puntaje total")

     plananalitico_id = fields.Many2one("das.plananalitico", string="Plan Analitico",
                                        default=lambda self: self.env['das.plananalitico'].search([], limit=1),
                                        group_expand='_group_expand_stage_ids',
                                        ondelete="cascade")


     _sql_constrainst = [
         ('name_unique', 'unique (name)',
          "El Nombre de Criterio de Evaluación ya Existe")
     ]

class Bibliografia(models.Model):
     _name = "das.bibliografia"
     _description = "Bibliografía"

     tipo = fields.Selection(selection=[("fisica", "Bibliografía Física"), ("virtual", "Bibliografía Virtual")],
                                        string= "Bibliografía", required = True)
     autor = fields.Char(string = "Autor")
     name = fields.Char(string = "Título")
     ciudad_pais = fields.Char(string = "Ciudad o país de Publicación")
     edicion = fields.Integer(string="Edición")
     editorial = fields.Char(string ="Editorial")
     anio_publicacion = fields.Integer(string="Año de Publicación")
     isbn = fields.Char(string="ISBN")
     direccion_electr = fields.Char(string = "Dirección electrónica")

class Unidad(models.Model):
     _name = "das.unidad"
     _description = "Unidad"

     name = fields.Char(string="Nombre de la Unidad", required = True)
     numero = fields.Integer(string = "Número de Unidad", required = True)
     horas = fields.Integer(string="Número de Horas", required = True)
     contenido_teorico = fields.Html(string="Contenido Teórico", required = True)
     horas_teorico = fields.Integer(string="Número de Horas Contenido Teórico", required = True)
     actividades_practicas = fields.Html(string="Actividades Prácticas", required = True)
     horas_practicas = fields.Integer(string="Número de horas contenido Práctico", required=True)
     aprendizaje_autonomo=fields.Html(string="Actividades de aprendizaje autónomo", required=True)
     horas_autonomo = fields.Integer(string="Número de horas actividades de aprendizaje autónomo", required = True)
     estrategias_evaluacion = fields.Html(string = "Estrategias de Evaluación", required = True)
     numero_sesiones = fields.Integer(string="Número de sesiones de la Unidad")

     silabo_id = fields.Many2one("das.silabo", string="Silabo")


     asignatura_id = fields.Many2one("das.asignatura", string="Asignatura")


class Sesion(models.Model):
     _name = "das.sesion"
     _description = "Sesión"

     name = fields.Char(string="Número de Sesión")
     fecha_inicio = fields.Date(string="Fecha de inicio de la sesión", required = True)
     fecha_fin= fields.Date(string="Fecha de finalización de la sesión", required = True)
     duracion= fields.Integer(string="Duración de la sesión", required = True)
     contenidos=fields.Html(string="Contenidos y Actividades de Aprendizaje Teórico", required = True)
     actividades_practicas=fields.Html(string="Actividades Prácticas", required = True)
     trabajo_autonomo=fields.Html(string="Actividades de Trabajo Autónomo", required = True)
     escenario_aprendizaje = fields.Html(string="escenario de Aprendizaje", required = True)

     silabo_id = fields.Many2one("das.silabo", string="Silabo")

class Contribucion(models.Model):
     _name = "das.contribucion"
     _description = "Relación de los contenidos de la asignatura con los resultados de aprendizaje"

     contenidos_asignatura = fields.Char(string="Contenidos de la Asignatura", required = True)
     contribucion = fields.Selection(selection=[("alta", "ALTA"), ("media", "MEDIA"),
                                       ("baja", "BAJA")],
                               string="Contribución",
                               default="alta")
     resultados_aprendizaje = fields.Html(string="Resultados de Aprendizaje", required = True)

     silabo_id = fields.Many2one("das.silabo", string="Silabo")



class PerfilEgreso(models.Model):
     _name = "das.perfilegreso"
     _description = "Relación de la Asignatura con los Resultados de Aprendizaje del Perfil de Egreso de la Carrera"

     resultado_aprendizajes = fields.Html(string="Resultados de Aprendizaje de la Asignatura", required = True)
     contribucion = fields.Selection(selection=[("alta", "ALTA"), ("media", "MEDIA"),
                                                ("baja", "BAJA")],
                                     string="Contribución",
                                     default="alta")
     perfil_egreso = fields.Html(string="Perfil de Egreso de la Carrera", required = True)

     silabo_id = fields.Many2one("das.silabo", string="Silabo")








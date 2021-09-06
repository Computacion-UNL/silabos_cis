{
    "name": "Diseño y Actualización de Sílabos de la Carrera de Ingeniería en Sistemas",
    "description": "Módulo de software para el Diseño y Actualización de Sílabos de la Carrera de Ingeniería en Sistemas de la UNL",
    "author": "Xavier Gordillo León",

    "summary": """
        Módulo de software para el Diseño y Actualización de Sílabos de la Carrera de Ingeniería en Sistemas de la Universidad Nacional de Loja
        """,

    "website": "https://unl.edu.ec/",

    "category": "Seguimiento",

    "version": "1.0",
    "depends": ["base", "mail"],
    "data": [
        "data/notificaciones_cron.xml",
        "data/mail_template.xml",
        "security/res_groups.xml",
        "security/ir_model_access.xml",
        "security/ir_rule.xml",
        "report/template.xml",
        "report/report.xml",
        "views/views.xml"
    ]
}
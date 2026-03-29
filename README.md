# NotarDigital
Sistema Digital para Notarías - Ley 21.772

# estructura proyecto
```
notaria_system/
│
├── app/
│   ├── __init__.py
│   ├── extensions.py
│   ├── models.py
│   ├── forms.py
│   ├── decorators.py
│   ├── utils.py
│   │
│   ├── routes/
│   │   ├── auth.py
│   │   ├── public.py
│   │   ├── admin.py
│   │   ├── documents.py
│   │   ├── complaints.py
│   │   ├── sanctions.py
│   │   └── audits.py
│   │
│   ├── templates/
│   │   ├── base.html
│   │   ├── public/
│   │   ├── auth/
│   │   ├── admin/
│   │   ├── documents/
│   │   ├── complaints/
│   │   ├── sanctions/
│   │   └── audits/
│   │
│   └── static/
│       └── css/
│
├── instance/
├── uploads/
│   ├── originals/
│   ├── signed/
│   ├── complaints/
│   └── copies/
│
├── config.py
├── run.py
└── requirements.txt
```
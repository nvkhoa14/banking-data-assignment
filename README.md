# banking-data-assignment
## OVERVIEW
1. About project
The project is designed and implemented a secure, compliant data platform for a simplified banking system which is guided by regulatory requirements from **2345/QĐ-NHNN 2023**, focusing on banking operations such as online/card-based payments, identity verification, device tracking, and fraud risk monitoring.
```text
banking-data-assignment
├── README.md
├── airflow
│   ├── dags
│   │   ├── banking_dq_dag.py
│   │   └── transaction_dag.py
│   ├── logs
│   └── plugins
├── dashboard
│   ├── dashboard.py
│   ├── dockerfile
│   └── requirements.txt
├── docker-compose.yml
├── img                                 # images for README.md
├── sql
│   ├── 01-init.sh
│   ├── dockerfile
│   └── schema.sql
└── src
    ├── data_quality_standards.py
    ├── dockerfile
    ├── generate_data.py
    ├── monitoring_audit.py
    └── requirements.txt
```
2. ERD
![ERD](./img/ERD.png)
3. Database
![DB](./img/DB.png)

## HOW TO RUN
- Docker verison >= 28.3.0
- Run docker-compose.
> docker-compose up -d --build

- Open http://localhost:8080/ and pass Username 'admin' and Password 'admin' to login screen.
![Login](./img/LOGIN.png)

- Active `banking-dq-workflow` DAG to generate data.
[GEN](./img/GEN%20DATA.png)

- After first DAG completed, Active `generate-transaction-every-minute` DAG to generate more transaction every minute. You can check the log to see how it handle transaction.
![LOG](./img/LOG.png)

- Interact with Psql DB.

> docker exec -it banking-db bash

> psql -U postgres -d banking

![Query](./img/QUERY.png)

- Open http://localhost:8051/ to access Streamlit visualization.

![DASHBOARD](./img/DASHBOARD.png)
![VIS](./img/VISUALIZATION.png)

- Stop docker and remove all containers and images.
> docker-compose down --rmi all --volumes --remove-orphans

- Or remove them in docker desktop.

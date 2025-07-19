# banking-data-assignment
## OVERVIEW
1. About project

2. ERD

3. Database

## HOW TO RUN
- Images
> docker build -t banking-postgres .

- Run image and create **banking** container
> sh run.sh

- Go to inside postgres
> docker exec -it banking-db bash
> psql -U postgres -d banking

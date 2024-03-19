# The TIRA Application

The backend server and frontend of the TIRA application.

## Development Setup

```bash
python3 src/manage.py migrate
python3 src/manage.py createcachetable
python3 src/manage.py makemigrations tira
python3 src/manage.py migrate tira 
python3 src/manage.py index_model
python3 src/manage.py loaddata mock-data/mock-data.json
python3 src/manage.py makemigrations
python3 src/manage.py migrate --fake
python3 src/manage.py run_develop
```

## Build and Deploy

### Step 1: Run the tests

   ```bash
   make tests # run all tests (automatically done in Github Actions on each commit)
   ```

### Step 2: Re-build the docker images: 

   ```bash
   ~$ make build-docker
   ~$ make build-docker-all
   ```

These make targets from the deployment configuration: `tira/application/config/settings-deploy.yml`

### Step 3: Deploy on Kubernetes

- `code-admin-knowledge-base/services/tira/` contains all the deployment yamls.
- Add the discourse secret in the namespace via: `tira-host/src/tira_scripts/k8s-deploy-discourse-api-key.sh`
   (this part is entirely deprecated and should be updated)


## Create New Zip of the Database Dump

Go the the password database `webis.uni-weimar.de:code-admin/passwords` -> Generic -> tira-development-database-dump

```
cd /mnt/ceph/storage/data-in-production/tira/development-database-dumps/
zip --encrypt django-db-dump-<DATE>.zip /mnt/ceph/tira/state/db-backup/django-db-dump-<DATE>.json
ln -s django-db-dump-<DATE>.zip django-db-dump.zip
```

## Troubleshooting

If there are problems with the precompiled protobuf parser, you can recompile them from the `tira/protocol` repository and copy them to `tira/application/src/tira/proto`. 

If you run into `django.db.utils.OperationalError: (1050, "Table <xy> already exists")`, skip migrations using `./venv/bin/python3 src/manage.py migrate --fake` .
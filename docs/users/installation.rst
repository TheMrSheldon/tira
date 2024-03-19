Installation
============
Docker Compose (recommended)
----------------------------

.. todo:: This guide currently does not work and only represents, how the installation *should* work in the future

.. code:: yaml

    version: "3.8"
    services:
        tira-backend:
            image: ghcr.io/tira-io/tira-backend
            ports: []                           # TODO
            depends_on:
                - database
                - auth
        tira-frontend:
            image: ghcr.io/tira-io/tira-frontend
            ports: []                           # TODO
            depends_on:
                - tira-backend
        database: {}                            # TODO
        auth:
            # We are using keycloak here. Other OIDC providers would of course work as well and
            # you can remove this, if you already have one, or replace it with your favorite one.
            image: quay.io/keycloak/keycloak:21.1.1
            restart: unless-stopped
            environment:
                - KEYCLOAK_ADMIN=admin          # CHANGE!!!! <- excessive use of ! to indicate urgency
                - KEYCLOAK_ADMIN_PASSWORD=admin # CHANGE!!!! <- excessive use of ! to indicate urgency
            ports:
                - "8080:8080"
            command:
                - start-dev

.. attention:: For improved security, it is highly recommended to place TIRA behind a reverse proxy.
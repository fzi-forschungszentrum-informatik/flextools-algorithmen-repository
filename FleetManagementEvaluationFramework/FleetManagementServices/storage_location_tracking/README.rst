FlexTools Storage Location Tracking
====================================

A containerized REST API and web UI for tracking unit loads across storage locations in a warehouse or buffer zone.
Part of the **FlexTools** software stack, developed at the `Institute for Information Management in Engineering (IMI) <https://www.imi.kit.edu>`_ at KIT.

----

Overview
--------

Storage Location Tracking (SLT) records every movement of physical unit loads (ULs) between storage locations.
It maintains a full movement history, computes current inventory quantities per item type, and exposes everything through a documented REST API.

Core concepts:

* **Item** — a product type, identified by a unique item number.
* **Unit Load (UL)** — a physical instance of an item that can be stored and retrieved.
* **Location** — a named physical storage position (station, vehicle, source, or sink).
* **UL Record** — a single storage event: which UL was stored at which location, and when it was retrieved.
* **Inventory History** — an automatically maintained time-series of item quantities.

----

Features
--------

* Full CRUD REST API for items, locations, unit loads, and UL records
* Store and retrieve unit loads with automatic timestamp tracking
* Real-time inventory quantity calculation per item
* Inventory history with point-in-time queries
* Web UI for browsing all data with search and server-side pagination
* Interactive REST API documentation (Swagger UI) at ``/api/v1``
* Seed data loading from JSON files on first startup (layout, items, records)
* Containerized with Docker Compose — single command to run

----

Requirements
------------

* `Docker <https://docs.docker.com/get-docker/>`_ with the Compose plugin (v2)

No other dependencies need to be installed on the host machine.

----

Quick Start
-----------

1. Clone the repository::

    git clone <repository-url>
    cd storagelocationtracking

2. Start the stack::

    docker compose up

3. Open the web UI: http://localhost:5000

4. Open the API documentation: http://localhost:5000/api/v1

On first startup, the application will:

* Wait for the PostgreSQL database to be ready
* Create all database tables
* Load seed data from the configured layout, items, and records JSON files (if ``LOAD_LAYOUT = True``)
* Generate the ``swagger.json`` specification file

----

Configuration
-------------

Application configuration lives in ``flextools_slt/instance/config.py``.
The ``DATABASE_URI`` can be overridden via the environment in ``docker-compose.yml``.

.. list-table::
   :widths: 30 15 55
   :header-rows: 1

   * - Setting
     - Default
     - Description
   * - ``DATABASE_URI``
     - ``postgresql://flextools_slt:flextools_slt@db/flextools_slt``
     - SQLAlchemy database connection string
   * - ``LOAD_LAYOUT``
     - ``True``
     - Whether to seed the database from JSON files on startup
   * - ``LAYOUT_FILE``
     - ``storage_location_tracking/layouts/wepa_lif.json``
     - Path to the location layout seed file (LIF JSON format)
   * - ``ITEMS_FILE``
     - ``storage_location_tracking/items/wepa_items.json``
     - Path to the items seed file
   * - ``RECORD_FILE``
     - ``storage_location_tracking/records/wepa_records.json``
     - Path to the UL records seed file

Seed files are located under ``flextools_slt/storage_location_tracking/``:

* ``layouts/`` — location layout definitions in LIF JSON format
* ``items/`` — item catalogue
* ``records/`` — initial unit load movement records

----

REST API
--------

The API is mounted at ``/api/v1``. Full interactive documentation (Swagger UI) is available at that path when the application is running.

.. list-table::
   :widths: 22 18 60
   :header-rows: 1

   * - Endpoint
     - Methods
     - Description
   * - ``/api/v1/items/``
     - GET POST PATCH DELETE
     - Manage item types. Filter by ``id`` or ``number``. Supports pagination.
   * - ``/api/v1/locations/``
     - GET POST PATCH DELETE
     - Manage storage locations. Filter by ``stationId``, ``stationName``, ``type``, ``itemId``, or ``ulId``.
   * - ``/api/v1/uls/``
     - GET POST PATCH DELETE
     - Manage unit loads. Filter by ``ulId``.
   * - ``/api/v1/uls/store``
     - POST
     - Store a unit load at a location. Identify by item number or UL ID plus location name.
   * - ``/api/v1/uls/retrieve``
     - POST
     - Retrieve a unit load. Pass ``finalRetrieval=true`` to mark the UL as completely retrieved.
   * - ``/api/v1/ulRecords/``
     - GET PATCH DELETE
     - Query movement records. Filter by ``locationId``, ``ulId``, ``start_date``, ``end_date``.
   * - ``/api/v1/inventory/``
     - GET
     - Query inventory history. Filter by ``item_id``, ``item_number``, or ``timestamp`` for point-in-time quantities.

All list endpoints accept ``page`` and ``per_page`` query parameters for pagination.

----

Project Structure
-----------------

::

    storagelocationtracking/
    ├── docker-compose.yml              # PostgreSQL + app service definitions
    ├── Dockerfile                      # Python 3.11 image, gunicorn entrypoint
    ├── requirements.txt
    └── flextools_slt/
        ├── entrypoint.sh               # DB init + gunicorn startup script
        ├── init_db.py                  # Creates tables, seeds data, saves swagger.json
        ├── wsgi.py                     # Gunicorn WSGI entry point
        └── storage_location_tracking/
            ├── __init__.py             # Flask app factory (create_app)
            ├── models.py               # SQLAlchemy models: Item, UL, ULRecord, Location, InventoryHistory
            ├── services.py             # Business logic: store/retrieve operations
            ├── layout_handler.py       # Bulk seed data loading from JSON files
            ├── blueprints/
            │   ├── api/                # Flask-RESTX namespaces (items, uls, locations, ulRecords, inventory)
            │   └── ui/                 # Jinja2 web UI (items, uls, ulhistory, locations)
            ├── layouts/                # Location layout seed files
            ├── items/                  # Item catalogue seed files
            └── records/                # UL record seed files

----

Technology Stack
----------------

* **Runtime**: Python 3.11
* **Web framework**: Flask 3 + Flask-RESTX (Swagger UI built-in)
* **ORM**: SQLAlchemy 2 + Flask-SQLAlchemy
* **Database**: PostgreSQL 17
* **Server**: Gunicorn
* **UI**: Bootstrap 5, DataTables, jQuery
* **Container**: Docker / Docker Compose

----

Development
-----------

The ``flextools_slt/`` directory is mounted as a volume in the Docker container, so code changes are reflected without rebuilding the image. Restart the container to reload Python modules::

    docker compose restart app

Rebuild the image after changing ``requirements.txt`` or the ``Dockerfile``::

    docker compose build
    docker compose up

----

Authors
-------

* Max Disselnmeyer — max.disselnmeyer@kit.edu
* Janik Bischoff — janik.bischoff@kit.edu

Institute for Information Management in Engineering (IMI), Karlsruhe Institute of Technology (KIT)

This project is funded by the European Union - NextGenerationEU - funding code 13IK032I and belongs to the FlexTools Software stack.
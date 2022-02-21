"""Module for creating the flask app."""
from datetime import datetime
from typing import Dict, Tuple, cast

from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import adapters.orm as orm
import adapters.repository as repository
import config
import domain.model as model
import service_layer.services as services

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint() -> Tuple[Dict[str, str], int]:
    """Endpoint for allocating an orderline to a batch."""
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    request_params_dict = cast(dict, request.json)
    try:
        orderid = request_params_dict["orderid"]
        sku = request_params_dict["sku"]
        qty = request_params_dict["qty"]
    except KeyError as e:
        return {"message": f"Missing the following input keys: {e}"}, 400
    except TypeError as e:
        return {
            "message": f"Could not retrieve parameters from an empty request: {e}."
            f"\n Please try again ith different parameters."
        }, 400

    try:
        batchref = services.allocate(orderid, sku, qty, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/add_batch", methods=["POST"])
def add_batch() -> Tuple[Dict[str, str], int]:
    """Function to add a batch to the database.

    Note: this is probably not a good name for a rest api.
    """
    session = get_session()
    repo = repository.SqlAlchemyRepository(session)
    request_params_dict = cast(dict, request.json)
    try:
        ref = request_params_dict["ref"]
        sku = request_params_dict["sku"]
        qty = request_params_dict["qty"]
        eta = request_params_dict["eta"]
        if eta is not None:
            eta = datetime.fromisoformat(eta).date()
    except KeyError as e:
        return {"message": f"Missing the following input keys: {e}"}, 400
    except TypeError as e:
        return {
            "message": f"Could not retrieve parameters from an empty request: {e}."
            f"\n Please try again ith different parameters."
        }, 400

    services.add_batch(
        ref,
        sku,
        qty,
        eta,
        repo,
        session,
    )
    return {"message": "OK"}, 201

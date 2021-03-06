"""Module for creating the flask app."""
from datetime import datetime
from typing import Dict, Optional, Tuple, cast

from flask import Flask, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.adapters.orm as orm
import app.config as config
import app.service_layer.handlers as handlers
from app.domain import commands
from app.service_layer import message_bus, unit_of_work

orm.start_mappers()
get_session = sessionmaker(bind=create_engine(config.get_postgres_uri()))
app = Flask(__name__)


@app.route("/allocate", methods=["POST"])
def allocate_endpoint() -> Tuple[Dict[str, Optional[str]], int]:
    """Endpoint for allocating an orderline to a batch."""
    request_params_dict = cast(dict, request.json)
    try:
        orderid = request_params_dict["orderid"]
        sku = request_params_dict["sku"]
        qty = request_params_dict["qty"]
        event = commands.Allocate(orderid, sku, qty)
    except KeyError as e:
        return {"message": f"Missing the following input keys: {e}"}, 400
    except TypeError as e:
        return {
            "message": f"Could not retrieve parameters from an empty request: {e}."
            f"\n Please try again ith different parameters."
        }, 400

    try:
        results = message_bus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
        batchref = results.pop(0)
    except (handlers.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201


@app.route("/add_batch", methods=["POST"])
def add_batch() -> Tuple[Dict[str, str], int]:
    """Function to add a batch to the database.

    Note: this is probably not a good name for a rest api.
    """
    request_params_dict = cast(dict, request.json)
    try:
        ref = request_params_dict["ref"]
        sku = request_params_dict["sku"]
        qty = request_params_dict["qty"]
        eta = request_params_dict["eta"]
        if eta is not None:
            eta = datetime.fromisoformat(eta).date()
        event = commands.CreateBatch(ref, sku, qty, eta)
    except KeyError as e:
        return {"message": f"Missing the following input keys: {e}"}, 400
    except TypeError as e:
        return {
            "message": f"Could not retrieve parameters from an empty request: {e}."
            f"\n Please try again ith different parameters."
        }, 400

    message_bus.handle(event, unit_of_work.SqlAlchemyUnitOfWork())
    return {"message": "OK"}, 201

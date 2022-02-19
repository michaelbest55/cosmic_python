"""Module for creating the flask app."""
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
        line = model.OrderLine(
            request_params_dict["orderid"],
            request_params_dict["sku"],
            request_params_dict["qty"],
        )
    except KeyError as e:
        return {"message": f"Missing the following input keys: {e}"}, 400
    except TypeError as e:
        return {
            "message": f"Could not retrieve parameters from an empty request: {e}."
            f"\n Please try again ith different parameters."
        }, 400

    try:
        batchref = services.allocate(line, repo, session)
    except (model.OutOfStock, services.InvalidSku) as e:
        return {"message": str(e)}, 400

    return {"batchref": batchref}, 201

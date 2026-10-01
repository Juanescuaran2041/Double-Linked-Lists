from flask import Blueprint, current_app, jsonify, request

from app.services import IncidentCase

api = Blueprint("api", __name__, url_prefix="/api")


def get_case() -> IncidentCase:
    return current_app.extensions["incident_case"]


@api.get("/timeline")
def get_timeline():
    return jsonify(get_case().snapshot())


@api.post("/events")
def add_event():
    case = get_case()
    event = case.add_evidence(request.get_json())
    return jsonify({"created": event.to_dict(), "timeline": case.snapshot()}), 201


@api.delete("/events/<event_id>")
def delete_event(event_id: str):
    case = get_case()
    case.remove_evidence(event_id)
    return jsonify(case.snapshot())


@api.post("/cursor/<action>")
def move_cursor(action: str):
    case = get_case()
    if action == "first":
        case.investigator.go_to_first()
    elif action == "last":
        case.investigator.go_to_last()
    elif action == "next":
        case.investigator.step_forward()
    elif action == "prev":
        case.investigator.step_backward()
    else:
        return jsonify({"message": f"Unknown action: {action}"}), 400
    return jsonify(case.snapshot())


@api.post("/cursor/jump/<event_id>")
def jump_cursor(event_id: str):
    case = get_case()
    case.investigator.jump_to(event_id)
    return jsonify(case.snapshot())


@api.get("/trace/backward")
def trace_backward():
    return jsonify(get_case().investigator.trace_to_patient_zero())


@api.get("/trace/forward")
def trace_forward():
    return jsonify(get_case().investigator.trace_impact())


@api.post("/clear")
def clear_case():
    case = get_case()
    case.clear()
    return jsonify(case.snapshot())


@api.errorhandler(KeyError)
def not_found(error):
    return jsonify({"message": str(error.args[0])}), 404


@api.errorhandler(ValueError)
def bad_request(error):
    return jsonify({"message": str(error)}), 400

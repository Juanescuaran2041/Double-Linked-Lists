from flask import Blueprint, jsonify, request

from app.services import IncidentCase

api = Blueprint("api", __name__, url_prefix="/api")
case = IncidentCase("IR-2026-0914 · Andes Freight Co.")


@api.get("/timeline")
def get_timeline():
    return jsonify(case.snapshot())


@api.post("/events")
def add_event():
    event = case.add_evidence(request.get_json())
    return jsonify({"created": event.to_dict(), "timeline": case.snapshot()}), 201


@api.delete("/events/<event_id>")
def delete_event(event_id: str):
    case.remove_evidence(event_id)
    return jsonify(case.snapshot())


@api.post("/events/<event_id>/move")
def move_event(event_id: str):
    data = request.get_json()
    case.move_evidence(event_id, data.get("before_id"))
    return jsonify(case.snapshot())


@api.post("/cursor/<action>")
def move_cursor(action: str):
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
    case.investigator.jump_to(event_id)
    return jsonify(case.snapshot())


@api.get("/trace/backward")
def trace_backward():
    return jsonify(case.investigator.trace_to_patient_zero())


@api.get("/trace/forward")
def trace_forward():
    return jsonify(case.investigator.trace_impact())


@api.post("/clear")
def clear_case():
    case.clear()
    return jsonify(case.snapshot())


@api.errorhandler(KeyError)
def not_found(error):
    return jsonify({"message": str(error.args[0])}), 404


@api.errorhandler(ValueError)
def bad_request(error):
    return jsonify({"message": str(error)}), 400

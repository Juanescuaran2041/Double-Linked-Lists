"""REST API consumed by the frontend."""

from flask import Blueprint, current_app, jsonify, request

from app.services import IncidentCase

api = Blueprint("api", __name__, url_prefix="/api")


def _case() -> IncidentCase:
    return current_app.extensions["incident_case"]


@api.get("/timeline")
def get_timeline():
    return jsonify(_case().snapshot())


@api.post("/events")
def add_event():
    body = request.get_json(force=True) or {}
    event = _case().add_evidence(body)
    return jsonify({"created": event.to_dict(), "timeline": _case().snapshot()}), 201


@api.delete("/events/<event_id>")
def delete_event(event_id: str):
    _case().remove_evidence(event_id)
    return jsonify(_case().snapshot())


@api.post("/cursor/<action>")
def move_cursor(action: str):
    investigator = _case().investigator
    actions = {
        "first": investigator.go_to_first,
        "last": investigator.go_to_last,
        "next": investigator.step_forward,
        "prev": investigator.step_backward,
    }
    if action not in actions:
        return jsonify({"error": f"Unknown action: {action}"}), 400
    actions[action]()
    return jsonify(_case().snapshot())


@api.post("/cursor/jump/<event_id>")
def jump_cursor(event_id: str):
    _case().investigator.jump_to(event_id)
    return jsonify(_case().snapshot())


@api.get("/trace/backward")
def trace_backward():
    return jsonify(_case().investigator.trace_to_patient_zero())


@api.get("/trace/forward")
def trace_forward():
    return jsonify(_case().investigator.trace_impact())


@api.post("/clear")
def clear_case():
    _case().clear()
    return jsonify(_case().snapshot())


# ---- error handling ----------------------------------------------------- #
@api.errorhandler(NotImplementedError)
def not_implemented(error: NotImplementedError):
    return jsonify({
        "error": "not_implemented",
        "method": str(error),
        "message": f"Implement {error} in app/models/attack_timeline.py",
    }), 501


@api.errorhandler(KeyError)
def not_found(error: KeyError):
    return jsonify({"error": "not_found", "message": str(error.args[0])}), 404


@api.errorhandler(ValueError)
def bad_request(error: ValueError):
    return jsonify({"error": "bad_request", "message": str(error)}), 400

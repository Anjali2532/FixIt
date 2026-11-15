"""Administrator management of maintenance contacts."""

from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError
from .extensions import db
from .models import StaffContact
from .security.access import require_role

staff = Blueprint("staff", __name__, url_prefix="/api/staff")


def public_contact(contact):
    return {
        "id": contact.id,
        "name": contact.full_name,
        "team": contact.team,
        "is_active": contact.is_active,
    }


@staff.get("")
@require_role("Administrator")
def list_contacts():
    contacts = db.session.scalars(
        db.select(StaffContact).order_by(
            StaffContact.is_active.desc(), StaffContact.full_name, StaffContact.id
        )
    ).all()
    return jsonify(contacts=[public_contact(contact) for contact in contacts])


@staff.post("")
@require_role("Administrator")
def create_contact():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(message="Enter the staff member’s name and team."), 400
    name, team = data.get("name"), data.get("team")
    if (
        not isinstance(name, str)
        or not 1 <= len(name.strip()) <= 100
        or not isinstance(team, str)
        or not 1 <= len(team.strip()) <= 80
    ):
        return (
            jsonify(
                message="Name must be 1–100 characters and team must be 1–80 characters."
            ),
            400,
        )
    contact = StaffContact(full_name=name.strip(), team=team.strip())
    try:
        db.session.add(contact)
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(message="That staff contact already exists."), 409
    return jsonify(contact=public_contact(contact)), 201


@staff.patch("/<int:contact_id>")
@require_role("Administrator")
def set_active(contact_id):
    contact = db.session.get(StaffContact, contact_id)
    if not contact:
        return jsonify(message="Staff contact not found."), 404
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or type(data.get("is_active")) is not bool:
        return jsonify(message="Choose active or inactive."), 400
    contact.is_active = data["is_active"]
    db.session.commit()
    return jsonify(contact=public_contact(contact))

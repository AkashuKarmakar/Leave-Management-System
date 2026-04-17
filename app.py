import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flasgger import Swagger
import portalocker

app = Flask(__name__)
# This creates the Swagger UI at /apidocs
swagger = Swagger(app)

DB_FILE = "database.json"

# --- Database Helpers ---

def read_db():
    if not os.path.exists(DB_FILE):
        return {"employees": [], "leaves": [], "balances": [], "metadata": {"lastEmployeeId": 0, "lastLeaveId": 0}}
    with portalocker.Lock(DB_FILE, mode='r', timeout=5) as f:
        return json.load(f)

def write_db(data):
    with portalocker.Lock(DB_FILE, mode='w', timeout=5) as f:
        json.dump(data, f, indent=2)

def api_response(success, message, data=None):
    return jsonify({
        "success": success,
        "message": message,
        "data": data
    })

# --- Routes ---

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """
    Fetch all employees or a specific one by ID.
    ---
    parameters:
      - name: employeeId
        in: query
        type: integer
    responses:
      200:
        description: A list of employees or a single employee
    """
    db = read_db()
    eid = request.args.get('employeeId')
    if eid:
        emp = next((e for e in db["employees"] if e["employeeId"] == int(eid)), None)
        if not emp:
            return api_response(False, "Employee not found"), 404
        return api_response(True, "Employee retrieved", emp)
    return api_response(True, "All employees retrieved", db["employees"])

@app.route('/api/employees', methods=['POST'])
def save_employee():
    """
    Create or Update an employee.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            employeeId: {type: integer}
            firstName: {type: string}
            lastName: {type: string}
            email: {type: string}
            department: {type: string}
            joinDate: {type: string}
    responses:
      200:
        description: Employee saved
    """
    db = read_db()
    data = request.json
    
    eid = data.get("employeeId")
    if eid:
        # Update
        for i, existing in enumerate(db["employees"]):
            if existing["employeeId"] == eid:
                db["employees"][i] = data
                write_db(db)
                return api_response(True, "Employee updated successfully", data)
        return api_response(False, "Employee ID not found"), 404
    else:
        # Create
        new_id = db["metadata"]["lastEmployeeId"] + 1
        data["employeeId"] = new_id
        db["employees"].append(data)
        db["metadata"]["lastEmployeeId"] = new_id
        write_db(db)
        return api_response(True, "Employee created successfully", data), 201

@app.route('/api/leaves/employee/<int:id>', methods=['GET'])
def get_leaves(id):
    """
    Get leave history for an employee.
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: status
        in: query
        type: string
    """
    db = read_db()
    status = request.args.get('status')
    leaves = [l for l in db["leaves"] if l["employeeId"] == id]
    if status:
        leaves = [l for l in leaves if l["status"].lower() == status.lower()]
    return api_response(True, f"Leaves for employee {id} retrieved", leaves)

@app.route('/api/leaves', methods=['POST'])
def submit_leave():
    """
    Submit a new leave request.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            employeeId: {type: integer}
            startDate: {type: string}
            endDate: {type: string}
            leaveType: {type: string}
            reason: {type: string}
    """
    db = read_db()
    data = request.json
    eid = data.get("employeeId")

    # Validate Employee
    if not any(e["employeeId"] == eid for e in db["employees"]):
        return api_response(False, "Employee does not exist"), 404

    # Calculate Days
    try:
        start = datetime.strptime(data["startDate"], "%Y-%m-%d")
        end = datetime.strptime(data["endDate"], "%Y-%m-%d")
        total_days = (end - start).days + 1
        if total_days <= 0:
            return api_response(False, "Invalid date range"), 400
    except Exception:
        return api_response(False, "Invalid date format. Use YYYY-MM-DD"), 400

    # Check Balance
    balance = next((b for b in db["balances"] if b["employeeId"] == eid and b["leaveType"].lower() == data["leaveType"].lower()), None)
    if not balance or (balance["quota"] - balance["used"]) < total_days:
        return api_response(False, "Insufficient balance"), 400

    # Save Leave
    new_id = db["metadata"]["lastLeaveId"] + 1
    leave_req = {
        "leaveId": new_id,
        "status": "Pending",
        "totalDays": total_days,
        **data
    }
    db["leaves"].append(leave_req)
    db["metadata"]["lastLeaveId"] = new_id
    write_db(db)
    
    return api_response(True, "Leave request submitted", leave_req), 201

@app.route('/api/leavebalances/employee/<int:id>/year/<int:year>', methods=['GET'])
def get_balance(id, year):
    db = read_db()
    balances = [b for b in db["balances"] if b["employeeId"] == id and b["year"] == year]
    return api_response(True, "Balances retrieved", balances)

# Required by document: Raw OpenAPI JSON
@app.route('/openapi.json')
def openapi():
    return jsonify(swagger.get_apispecs())

if __name__ == '__main__':
    app.run(debug=True, port=8000)
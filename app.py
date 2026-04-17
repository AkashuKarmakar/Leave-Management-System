import json
import os
from datetime import datetime
from flask import Flask, request, jsonify
from flasgger import Swagger
import portalocker

app = Flask(__name__)
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
    return jsonify({"success": success, "message": message, "data": data})

# --- Routes ---

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """
    Retrieve all employees or a specific employee by ID.
    ---
    parameters:
      - name: employeeId
        in: query
        type: integer
        description: ID of the employee to fetch
    responses:
      200:
        description: Success
    """
    db = read_db()
    eid = request.args.get('employeeId')
    if eid:
        emp = next((e for e in db["employees"] if str(e["employeeId"]) == str(eid)), None)
        if not emp: return api_response(False, "Employee not found"), 404
        return api_response(True, "Employee retrieved", emp)
    return api_response(True, "All employees retrieved", db["employees"])

@app.route('/api/employees', methods=['POST'])
def save_employee():
    """
    Create a new employee or update an existing one.
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          properties:
            employeeId: {type: integer, description: "Leave blank to create new"}
            firstName: {type: string}
            lastName: {type: string}
            email: {type: string}
            department: {type: string}
            joinDate: {type: string, description: "YYYY-MM-DD"}
    responses:
      200:
        description: Success
    """
    db = read_db()
    data = request.json
    eid = data.get("employeeId")
    if eid:
        # Update Logic
        for i, existing in enumerate(db["employees"]):
            if existing["employeeId"] == eid:
                db["employees"][i] = data
                write_db(db)
                return api_response(True, "Employee updated successfully", data)
        return api_response(False, f"Employee ID {eid} not found for update"), 404
    else:
        # Create Logic
        new_id = db["metadata"]["lastEmployeeId"] + 1
        data["employeeId"] = new_id
        db["employees"].append(data)
        db["metadata"]["lastEmployeeId"] = new_id
        write_db(db)
        return api_response(True, "Employee created successfully", data), 201

@app.route('/api/leaves/employee/<int:id>', methods=['GET'])
def get_leaves(id):
    """
    Get leave history for a specific employee.
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: status
        in: query
        type: string
        description: Filter by status (Pending, Approved, Rejected)
    responses:
      200:
        description: Success
    """
    db = read_db()
    leaves = [l for l in db["leaves"] if l["employeeId"] == id]
    status = request.args.get('status')
    if status:
        leaves = [l for l in leaves if l["status"].lower() == status.lower()]
    return api_response(True, f"Found {len(leaves)} leaves", leaves)

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
          properties:
            employeeId: {type: integer}
            startDate: {type: string, description: "YYYY-MM-DD"}
            endDate: {type: string, description: "YYYY-MM-DD"}
            leaveType: {type: string, description: "Annual, Sick, or Casual"}
            reason: {type: string}
    responses:
      201:
        description: Created
    """
    db = read_db()
    data = request.json
    eid = data.get("employeeId")

    if not any(e["employeeId"] == eid for e in db["employees"]):
        return api_response(False, f"Error: Employee ID {eid} does not exist."), 404

    try:
        start = datetime.strptime(data["startDate"], "%Y-%m-%d")
        end = datetime.strptime(data["endDate"], "%Y-%m-%d")
        total_days = (end - start).days + 1
        year = start.year
        if total_days <= 0:
            return api_response(False, "Error: End date must be after Start date"), 400
    except Exception:
        return api_response(False, "Error: Use YYYY-MM-DD format"), 400

    balance = next((b for b in db["balances"] 
                    if b["employeeId"] == eid 
                    and b["leaveType"].lower() == data["leaveType"].lower()
                    and b["year"] == year), None)
    
    if not balance:
        return api_response(False, f"Error: No quota for {data['leaveType']} found in {year}"), 400
    
    if total_days > (balance["quota"] - balance["used"]):
        return api_response(False, "Error: Insufficient balance."), 400

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
    return api_response(True, "Leave request submitted successfully", leave_req), 201

@app.route('/api/leavebalances/employee/<int:id>/year/<int:year>', methods=['GET'])
def get_balance(id, year):
    """
    Check leave balances for an employee in a specific year.
    ---
    parameters:
      - name: id
        in: path
        type: integer
        required: true
      - name: year
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Success
    """
    db = read_db()
    balances = [b for b in db["balances"] if b["employeeId"] == id and b["year"] == year]
    return api_response(True, "Balances retrieved", balances)

if __name__ == '__main__':
    app.run(debug=True, port=8000)
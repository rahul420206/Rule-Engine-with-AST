from flask import Flask, request, render_template, session, jsonify  # Flask's session is used for web session handling
from models import Node, Rule
from utils import parse_tokens_to_ast, tokenize_rule
from models import UserInput
import re
from database import db_session  # Ensure your imports are correct
import json

app = Flask(__name__)

app.secret_key = '45c77489c303be0a79e3ec0d1accd937'

class Node:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type  # "operator" or "operand"
        self.value = value  # Operand value, like "age > 30"
        self.left = left  # Left child node
        self.right = right  # Right child node

    def to_dict(self):
        return {
            'node_type': self.node_type,
            'value': self.value,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

    @staticmethod
    def from_dict(data):
        if data is None:
            return None
        node = Node(data.get('node_type'), data.get('value'))
        node.left = Node.from_dict(data.get('left'))
        node.right = Node.from_dict(data.get('right'))
        return node

def evaluate_condition(condition, data):
    """Evaluates a condition like 'age > 30' or 'department = Sales' using the provided data."""
    attribute, operator, value = parse_condition(condition)
    print(f"Parsing condition: {condition} => Attribute: {attribute}, Operator: {operator}, Value: {value}")

    if attribute not in data:
        return False

    attribute_value = data[attribute]

    # Handle string values and case-insensitive comparison
    if isinstance(attribute_value, str) and isinstance(value, str):
        attribute_value = attribute_value.strip().lower()
        value = value.strip().lower()

    # Perform the comparison based on the operator
    try:
        if operator == '>':
            return float(attribute_value) > float(value)
        elif operator == '<':
            return float(attribute_value) < float(value)
        elif operator == '>=':
            return float(attribute_value) >= float(value)
        elif operator == '<=':
            return float(attribute_value) <= float(value)
        elif operator == '=':
            return attribute_value == value  # Explicitly return True if condition matches
        else:
            return False
    except ValueError:
        # Handle cases where the data types don't match properly
        return False
    
def evaluate_ast(ast, data):
    """Recursively evaluates the AST against the data."""
    if ast is None:
        return False

    # If the current node is a condition (operand), evaluate it directly
    if ast.node_type == "operand":
        result = evaluate_condition(ast.value, data)
        print(f"Evaluating condition: {ast.value} => {result}")
        return result

    # If the current node is an operator (AND/OR), evaluate both sides
    elif ast.node_type == "operator":
        left_result = evaluate_ast(ast.left, data) if ast.left else False
        right_result = evaluate_ast(ast.right, data) if ast.right else False
        print(f"Evaluating operator: {ast.value} with Left: {left_result}, Right: {right_result}")

        # Handle logical operations correctly
        if ast.value == "AND":
            return left_result and right_result  # Explicitly return True if both sides are True
        elif ast.value == "OR":
            return left_result or right_result  # Explicitly return True if at least one side is True

    return False

rules_db = {} 

@app.route('/create_rule', methods=['POST'])
def create_rule():
    data = request.json
    rule_string = data.get('rule_string')
    if not rule_string:
        return jsonify({'error': 'No rule provided'}), 400

    # Generate a simple rule ID
    rule_id = str(len(rules_db) + 1)
    rules_db[rule_id] = {'rule_string': rule_string}
    
    return jsonify({'message': 'Rule added successfully'}), 200

@app.route('/rules', methods=['GET'])
def get_rules():
    return jsonify(rules_db), 200

@app.route('/delete_rule/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    if rule_id in rules_db:
        del rules_db[rule_id]
        return jsonify({'message': 'Rule deleted successfully'}), 200
    else:
        return jsonify({'error': 'Rule not found'}), 404
    
@app.route('/combine_rules', methods=['POST'])
def combine_rules():
    data = request.json
    rule_ids = data.get('rule_ids')
    operator = data.get('operator', 'AND')

    if not rule_ids or len(rule_ids) < 2:
        return jsonify({'error': 'At least two rules are required to combine'}), 400

    try:
        combined_rule_string = f" {operator} ".join(
            f"({rules_db[rule_id]['rule_string']})" for rule_id in rule_ids if rule_id in rules_db
        )
        return jsonify({'combined_rule': combined_rule_string}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to combine rules: {str(e)}'}), 500

def parse_condition(condition):
    """Parses a condition string like 'age > 30' and returns the attribute, operator, and value."""
    match = re.match(r'(\w+)\s*(>|<|=|>=|<=)\s*([\'"]?[\w\s]+[\'"]?)', condition)
    if match:
        attribute = match.group(1)
        operator = match.group(2)
        value = match.group(3).strip("'\"")  # Remove quotes from the value if present
        return attribute, operator, value
    return None, None, None

@app.route('/')
def home():
    # Get the rule stored in Flask's session, if it exists
    rule_text = session.get('rule_text', 'No conditions added yet.')  # Use Flask's session, not SQLAlchemy's
    return render_template('index.html', rule_text=rule_text)


@app.route('/evaluate_rule_form', methods=['POST'])
def evaluate_rule_form():
    age = request.form.get('age')
    department = request.form.get('department')
    salary = request.form.get('salary')
    experience = request.form.get('experience')

    # Check if any of the fields are empty and handle the error
    if not age or not salary or not experience or not department:
        return render_template('index.html', error='Please fill in all required fields.')

    try:
        # Convert form input to appropriate data types
        data = {
            'age': int(age),
            'department': department,
            'salary': int(salary),
            'experience': int(experience)
        }
    except ValueError:
        return render_template('index.html', error='Invalid data provided. Please enter valid numbers.')

    # Retrieve AST from the Flask session
    ast_data = session.get('ast_data')
    if not ast_data:
        return render_template('index.html', error='No rule found. Please create a rule first.')

    # Convert JSON string back to a dictionary
    try:
        ast_dict = json.loads(ast_data)
        ast = Node.from_dict(ast_dict)  # Use the converted dictionary
    except json.JSONDecodeError:
        return render_template('index.html', error='Error decoding the stored rule. Please recreate the rule.')

    # Evaluate the AST against the user-provided data
    result = evaluate_ast(ast, data)

    # If the input satisfies the rule, store it in the database
    if result:
        new_user_input = UserInput(
            age=data['age'],
            department=data['department'],
            salary=data['salary'],
            experience=data['experience']
        )
        db_session.add(new_user_input)
        db_session.commit()

    # Fetch all stored inputs from the database
    stored_inputs = db_session.query(UserInput).all()

    # Render the result back to the template
    return render_template(
        'index.html',
        age=data['age'],
        department=data['department'],
        salary=data['salary'],
        experience=data['experience'],
        result=f'Result: {result}',
        stored_inputs=stored_inputs
    )



def generate_rule_text(ast):
    """Generates a human-readable string representation of the AST."""
    if ast is None:
        return ""
    if ast.node_type == "operand":
        return ast.value
    elif ast.node_type == "operator":
        left_text = generate_rule_text(ast.left)
        right_text = generate_rule_text(ast.right)
        return f"({left_text} {ast.value} {right_text})"
    
def combine_asts(ast_list, operator="AND"):
    """
    Combine a list of ASTs using a logical operator.
    
    Parameters:
    - ast_list: A list of ASTs to be combined.
    - operator: A string representing the logical operator, e.g., "AND" or "OR".
    
    Returns:
    - A single AST representing the combination of the provided ASTs.
    """
    if not ast_list:
        raise ValueError("The AST list is empty")

    # If there is only one AST, return it directly.
    if len(ast_list) == 1:
        return ast_list[0]

    # Create a new combined AST node using the provided operator.
    combined_ast = {
        "type": "LogicalExpression",
        "operator": operator,
        "left": ast_list[0],
        "right": ast_list[1]
    }

    # Combine multiple ASTs iteratively if there are more than 2.
    for ast in ast_list[2:]:
        combined_ast = {
            "type": "LogicalExpression",
            "operator": operator,
            "left": combined_ast,
            "right": ast
        }

    return combined_ast

    
@app.route('/combine_rules', methods=['POST'])
def combine_rules_endpoint():
    data = request.json
    rule_ids = data.get('rule_ids')
    operator = data.get('operator', 'AND')

    if not rule_ids or len(rule_ids) < 2:
        return jsonify({'error': 'At least two rules are required to combine'}), 400

    try:
        combined_rule_string = f" {operator} ".join(
            f"({rules_db[rule_id]['rule_string']})" for rule_id in rule_ids if rule_id in rules_db
        )
        return jsonify({'combined_rule': combined_rule_string}), 200
    except Exception as e:
        return jsonify({'error': f'Failed to combine rules: {str(e)}'}), 500



if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, request, jsonify, session
import json

app = Flask(__name__)
app.secret_key = '45c77489c303be0a79e3ec0d1accd937'

# In-memory storage for rules
rules_storage = {}

# Utility to generate unique rule IDs
def generate_rule_id():
    return str(len(rules_storage) + 1)

# Tokenize rule and parse to AST placeholder functions
def tokenize_rule(rule):
    # Replace with your actual tokenization logic
    return rule.split()

def parse_tokens_to_ast(tokens):
    # Replace with your actual AST parsing logic
    return {'type': 'Rule', 'tokens': tokens}

# Combine ASTs
def combine_asts(ast_list, operator="AND"):
    if not ast_list:
        raise ValueError("The AST list is empty")

    if len(ast_list) == 1:
        return ast_list[0]

    combined_ast = {
        "type": "LogicalExpression",
        "operator": operator,
        "left": ast_list[0],
        "right": ast_list[1]
    }

    for ast in ast_list[2:]:
        combined_ast = {
            "type": "LogicalExpression",
            "operator": operator,
            "left": combined_ast,
            "right": ast
        }

    return combined_ast

# Endpoint to create a new rule
@app.route('/create_rule', methods=['POST'])
def create_rule():
    rule_string = request.json.get('rule_string')
    if not rule_string:
        return jsonify({'error': 'No rule provided'}), 400

    rule_id = generate_rule_id()
    tokens = tokenize_rule(rule_string)
    ast = parse_tokens_to_ast(tokens)
    
    # Store rule in memory
    rules_storage[rule_id] = {
        'rule_string': rule_string,
        'ast': ast
    }

    return jsonify({'rule_id': rule_id, 'rule': rule_string, 'ast': ast}), 201

# Endpoint to get all rules
@app.route('/rules', methods=['GET'])
def get_rules():
    return jsonify(rules_storage), 200

# Endpoint to combine rules
@app.route('/combine_rules', methods=['POST'])
def combine_rules():
    rule_ids = request.json.get('rule_ids')
    operator = request.json.get('operator', 'AND')

    if not rule_ids or not isinstance(rule_ids, list):
        return jsonify({'error': 'No rule IDs provided'}), 400

    try:
        # Fetch ASTs for the provided rule IDs
        ast_list = [rules_storage[rule_id]['ast'] for rule_id in rule_ids if rule_id in rules_storage]
        if len(ast_list) != len(rule_ids):
            return jsonify({'error': 'One or more rule IDs not found'}), 404

        # Combine ASTs using the specified operator
        combined_ast = combine_asts(ast_list, operator)

        combined_rule_string = f" {operator} ".join(f"({rules_storage[rule_id]['rule_string']})" for rule_id in rule_ids)
        session['combined_ast'] = json.dumps(combined_ast)

        return jsonify({
            'combined_rule': combined_rule_string,
            'ast': combined_ast
        })
    except Exception as e:
        return jsonify({'error': f'Failed to combine rules: {str(e)}'}), 500

# Endpoint to update a rule
@app.route('/update_rule/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    if rule_id not in rules_storage:
        return jsonify({'error': 'Rule ID not found'}), 404

    new_rule_string = request.json.get('rule_string')
    if not new_rule_string:
        return jsonify({'error': 'No rule provided'}), 400

    tokens = tokenize_rule(new_rule_string)
    new_ast = parse_tokens_to_ast(tokens)

    # Update rule in storage
    rules_storage[rule_id] = {
        'rule_string': new_rule_string,
        'ast': new_ast
    }

    return jsonify({'rule_id': rule_id, 'updated_rule': new_rule_string, 'ast': new_ast}), 200

# Endpoint to delete a rule
@app.route('/delete_rule/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    if rule_id not in rules_storage:
        return jsonify({'error': 'Rule ID not found'}), 404

    # Remove rule from storage
    del rules_storage[rule_id]

    return jsonify({'message': f'Rule {rule_id} deleted successfully'}), 200

if __name__ == '__main__':
    app.run(debug=True)

from sqlalchemy import Column, Integer, String, Text
from database import Base  # Import the correct Base class for SQLAlchemy

class UserInput(Base):
    __tablename__ = 'user_inputs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    age = Column(Integer, nullable=False)
    department = Column(String, nullable=False)
    salary = Column(Integer, nullable=False)
    experience = Column(Integer, nullable=False)

    def __repr__(self):
        return f"<UserInput(age={self.age}, department='{self.department}', salary={self.salary}, experience={self.experience})>"


class Rule(Base):
    __tablename__ = 'rules'
    id = Column(Integer, primary_key=True)
    rule_string = Column(String, nullable=False)
    ast = Column(Text)  # Store the AST as a JSON string

    def __repr__(self):
        return f'<Rule {self.rule_string}>'

class Node:
    def __init__(self, node_type, value=None, left=None, right=None):
        self.node_type = node_type  # "operator" or "operand"
        self.value = value  # Operand value, like "age > 30" or operator like "AND"/"OR"
        self.left = left  # Left child node for AST structure
        self.right = right  # Right child node for AST structure

    def to_dict(self):
        # Converts the Node to a dictionary for easy storage in JSON format
        return {
            'node_type': self.node_type,
            'value': self.value,
            'left': self.left.to_dict() if self.left else None,
            'right': self.right.to_dict() if self.right else None
        }

    @staticmethod
    def from_dict(data):
        # Rebuilds a Node object from its dictionary representation
        if data is None:
            return None
        node = Node(data.get('node_type'), data.get('value'))
        node.left = Node.from_dict(data.get('left'))
        node.right = Node.from_dict(data.get('right'))
        return node

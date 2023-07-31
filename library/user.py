import os

class User:
    unique_users = set()  # Initialize unique_users here

    def __init__(self, user_id):
        self.id = user_id

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if isinstance(other, User):
            return self.id == other.id
        return False

if os.path.exists('unique_users.txt'):
    with open('unique_users.txt', 'r') as f:
        for line in f:
            user_id = line.strip()
            User.unique_users.add(User(user_id))
else:
    User.unique_users = set()


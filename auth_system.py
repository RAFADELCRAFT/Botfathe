import json
import os
from typing import Dict, List, Set

class AuthSystem:
    def __init__(self, admin_id: int, allowed_group: int):
        self.admin_id = admin_id
        self.allowed_group = allowed_group
        self.authorized_users: Set[int] = set()
        self.gratis_mode = False  # Default: only authorized users can use
        
        # Load existing data
        self.load_data()
    
    def load_data(self):
        """Load authorization data from file"""
        if os.path.exists('auth_data.json'):
            try:
                with open('auth_data.json', 'r') as f:
                    data = json.load(f)
                    self.authorized_users = set(data.get('authorized_users', []))
                    self.gratis_mode = data.get('gratis_mode', False)
            except:
                self.authorized_users = set()
                self.gratis_mode = False
    
    def save_data(self):
        """Save authorization data to file"""
        data = {
            'authorized_users': list(self.authorized_users),
            'gratis_mode': self.gratis_mode
        }
        with open('auth_data.json', 'w') as f:
            json.dump(data, f, indent=2)
    
    def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id == self.admin_id
    
    def is_authorized(self, user_id: int) -> bool:
        """Check if user is authorized"""
        return user_id in self.authorized_users
    

    def can_use_bot(self, user_id: int, chat_id: int, is_private: bool | None = None) -> bool:
        """Compat: si no se pasa `is_private`, lo inferimos por el id del chat (>0 privado)."""
        user_id = int(user_id)
        chat_id = int(chat_id)
        if is_private is None:
            try:
                is_private = chat_id > 0
            except Exception:
                is_private = False

        if self.gratis_mode:
            return True

        if is_private:
            return self.is_authorized(user_id)

        if self.allowed_group is not None:
            return chat_id == self.allowed_group
        return True
    def add_user(self, user_id: int) -> bool:
        """Add user to authorized list"""
        self.authorized_users.add(user_id)
        self.save_data()
        return True
    
    def remove_user(self, user_id: int) -> bool:
        """Remove user from authorized list"""
        if user_id in self.authorized_users:
            self.authorized_users.remove(user_id)
            self.save_data()
            return True
        return False
    
    def set_gratis_mode(self, enabled: bool):
        """Enable/disable gratis mode"""
        self.gratis_mode = enabled
        self.save_data()
    
    def get_authorized_users(self) -> List[int]:
        """Get list of authorized users"""
        return list(self.authorized_users)
    
    def get_stats(self) -> Dict:
        """Get authorization statistics"""
        return {
            'total_authorized': len(self.authorized_users),
            'gratis_mode': self.gratis_mode,
            'allowed_group': self.allowed_group
        }

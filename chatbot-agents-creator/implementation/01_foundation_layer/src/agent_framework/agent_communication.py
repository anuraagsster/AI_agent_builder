class AgentCommunication:
    def __init__(self):
        self.message_handlers = {}
        
    def register_message_handler(self, message_type, handler):
        """Register a handler for a specific message type"""
        self.message_handlers[message_type] = handler
        
    def send_message(self, recipient, message_type, content):
        """Send a message to another agent"""
        pass
        
    def receive_message(self, sender, message_type, content):
        """Process a received message"""
        if message_type in self.message_handlers:
            return self.message_handlers[message_type](sender, content)
        return None
        
    def broadcast_message(self, message_type, content):
        """Send a message to all connected agents"""
        pass
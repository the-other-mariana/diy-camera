class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None

    def delete_node(self, node_to_delete):
        if self.head is None or node_to_delete is None: 
            return
    
        if self.head == node_to_delete: 
            self.head = node_to_delete.next

        if node_to_delete.next is not None: 
            node_to_delete.next.prev = node_to_delete.prev 

        if node_to_delete.prev is not None: 
            node_to_delete.prev.next = node_to_delete.next

    def push(self, new_data): 
        new_node = Node(new_data)
        new_node.prev = self.head

        if self.head is not None: 
            self.head.next = new_node 

        self.head = new_node
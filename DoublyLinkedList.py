class Node:
    def __init__(self, data):
        self.data = data
        self.next = None
        self.prev = None

class DoublyLinkedList:
    def __init__(self):
        self.tail = None
        self.head = None

    def delete_node(self, node_to_delete):
        # case: empty list
        if self.head is None or node_to_delete is None: 
            return
    
        # case: the node is the last one
        if self.tail == node_to_delete: 
            node_to_delete.prev.next = self.head
            self.tail = node_to_delete.prev


        # case: the node is the first one
        if self.head == node_to_delete:
            node_to_delete.prev.prev = self.tail
            self.head = node_to_delete.next

        # case: normal
        # modify the node's next ref
        if node_to_delete.next != None and node_to_delete.prev != None: 
            node_to_delete.next.prev = node_to_delete.prev 

        # case: normal
        # modify the node's prev ref
        if node_to_delete.prev != None and node_to_delete.next != None: 
            node_to_delete.prev.next = node_to_delete.next

    def push(self, new_data): 
        new_node = Node(new_data)
        new_node.prev = self.tail

        # case: adding the first element
        if self.head == None:
            self.head = new_node
            self.tail = new_node

        if self.tail != None: 
            self.tail.next = new_node 

        self.tail = new_node
# coding: utf-8

"""
设计链表存储
"""


class Node(object):

    def __init__(self, data, prev=None, next_=None):
        self.data = data
        self.prev = prev
        self.next_ = next_

    def __str__(self):
        return self.data


class LinkedList(object):

    def __init__(self, head=None):
        self.head = head
        self.size = 0

    def __len__(self):
        pass

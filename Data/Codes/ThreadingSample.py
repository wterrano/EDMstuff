__author__ = 'William'

import threading
import time


def get_thread_name():
    t = threading.current_thread()
    return t.name


def print_time(delay):
    """Define a function for the thread."""
    thread_name = get_thread_name()
    count = 0
    while count < 8:
        time.sleep(delay)
        count += 1
        print("%s: %s" % (thread_name, time.ctime(time.time())))


# Create two threads as follows
t1 = threading.Thread(target=print_time, args=(1,))
t2 = threading.Thread(target=print_time, args=(2,))
t1.start()
t2.start()
t1.join()
t2.join()


import math

_author_ = 'wombat'
_project_ = 'MySimplePythonApplication'
#
# class Solver:
#     def demo(self):
#         while True:
#             a = int(input("a "))
#             b = int(input("b "))
#             c = int(input("c "))
#             d = b ** 2 - 4 * a * c
#             if d>=0:
#                 disc = math.sqrt(d)
#                 root1 = (-b + disc) / (2 * a)
#                 root2 = (-b - disc) / (2 * a)
#                 print(root1, root2)
#             else:
#                 print('error')
#
# Solver().demo()

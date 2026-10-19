#!/usr/bin/env python3
"""
Simple Todo CLI application.
Usage:
  python main.py add "todo text"
  python main.py list

Todos are stored in 'todos.json' in the same directory.
"""
import argparse
import json
import os
import sys
from datetime import datetime

TODO_FILE = os.path.join(os.path.dirname(__file__), 'todos.json')


def load_todos():
    if not os.path.exists(TODO_FILE):
        return []
    try:
        with open(TODO_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def save_todos(todos):
    with open(TODO_FILE, 'w', encoding='utf-8') as f:
        json.dump(todos, f, ensure_ascii=False, indent=2)


def add_todo(text):
    todos = load_todos()
    todo = {
        'id': (todos[-1]['id'] + 1) if todos else 1,
        'text': text,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    todos.append(todo)
    save_todos(todos)
    print(f"Added todo #{todo['id']}: {todo['text']}")


def list_todos():
    todos = load_todos()
    if not todos:
        print('No todos yet. Add one with: python main.py add "Buy milk"')
        return
    for t in todos:
        created = t.get('created_at', '')
        print(f"#{t['id']}: {t['text']} (created: {created})")


def parse_args(argv):
    parser = argparse.ArgumentParser(description='Simple Todo CLI')
    sub = parser.add_subparsers(dest='cmd')

    addp = sub.add_parser('add', help='Add a new todo')
    addp.add_argument('text', nargs='+', help='Text of the todo')

    sub.add_parser('list', help='List todos')

    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    if not args.cmd:
        print('No command specified. Use "add" or "list". Try -h for help.')
        return 1

    if args.cmd == 'add':
        text = ' '.join(args.text).strip()
        if not text:
            print('Cannot add empty todo.')
            return 1
        add_todo(text)
        return 0
    elif args.cmd == 'list':
        list_todos()
        return 0
    else:
        print('Unknown command')
        return 1

if __name__ == '__main__':
    raise SystemExit(main())

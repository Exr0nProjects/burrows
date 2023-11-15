from sys import argv
from json import loads
from rich.console import Console
console = Console()

console.print(argv[1])
console.print(loads(argv[1]))



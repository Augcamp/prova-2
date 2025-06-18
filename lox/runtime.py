import builtins
from dataclasses import dataclass
from operator import add, eq, ge, gt, le, lt, mul, ne, neg, not_, sub, truediv
from typing import TYPE_CHECKING

from .ctx import Ctx

if TYPE_CHECKING:
    from .ast import Block, Stmt, Value

__all__ = [
    "add",
    "eq",
    "ge",
    "gt",
    "le",
    "lt",
    "mul",
    "ne",
    "neg",
    "not_",
    "print",
    "show",
    "sub",
    "truthy",
    "truediv",
]


class LoxInstance:
    """
    Classe base para todos os objetos Lox.
    """


@dataclass
class LoxFunction:
    """Representa uma função Lox que pode ser chamada."""
    name: str
    params: list[str]
    body: "Block" 
    closure: Ctx

    def __call__(self, *args: "Value") -> "Value":
        return self.call(list(args))

    def call(self, args: list["Value"]) -> "Value":

        if len(args) != len(self.params):
            raise TypeError(
                f"Expected {len(self.params)} arguments but got {len(args)}."
            )


        ctx = Ctx(scope={}, parent=self.closure)


        for param_name, arg_value in zip(self.params, args):

            ctx.var_def(param_name, arg_value)


        try:
            self.body.eval(ctx)
        except LoxReturn as ret:
            return ret.value


        return None


class LoxReturn(Exception):
    """
    Exceção para retornar de uma função Lox.
    """
    def __init__(self, value):
        self.value = value
        super().__init__()


class LoxError(Exception):
    """
    Exceção para erros de execução Lox.
    """



nan = float("nan")
inf = float("inf")


def floordiv(a, b):
    return a // b

def print(value: "Value"):
    """Imprime um valor lox."""
    builtins.print(show(value))

def show(value: "Value") -> str:
    """Converte valor lox para string."""
    return str(value)

def show_repr(value: "Value") -> str:
    """Mostra um valor lox, mas coloca aspas em strings."""
    if isinstance(value, str):
        return f'"{value}"'
    return show(value)

def truthy(value: "Value") -> bool:
    """Converte valor lox para booleano segundo a semântica do lox."""
    if value is None or value is False:
        return False
    return True
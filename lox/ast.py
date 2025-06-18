from abc import ABC
from dataclasses import dataclass
from typing import Callable

from .ctx import Ctx
from .node import Node
from .runtime import LoxReturn, LoxFunction


Value = bool | str | float | None

def is_implicit_int(name: str) -> bool:
    return name and name[0] in "ijklmn"

def auto_convert(name: str, value: Value) -> Value:
    if is_implicit_int(name):
        if isinstance(value, str) and value.isdigit():
            return int(value)
        if isinstance(value, float):
            return int(value)
        if isinstance(value, bool):
            return int(value)
    return value




def is_truthy(value: Value) -> bool:
    """
    Verifica se um valor é "verdadeiro" de acordo com as regras do Lox.
    Apenas `nil` e `false` são considerados falsos.
    """
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    return True


def lox_str(value: Value) -> str:
    """
    Converte um valor Lox para a sua representação em string correta.
    """
    if value is None:
        return "nil"
    if isinstance(value, bool):
        return str(value).lower()  
    if isinstance(value, float) and value.is_integer():
        return str(int(value)) 
    return str(value)



class Expr(Node, ABC):
    """Classe base para expressões."""

class Stmt(Node, ABC):
    """Classe base para comandos."""

@dataclass
class Program(Node):
    """Representa um programa."""
    stmts: list[Stmt]

    def eval(self, ctx: Ctx):
        for stmt in self.stmts:
            stmt.eval(ctx)

@dataclass
class DoWhileStmt(Stmt):
    body: Stmt
    condition: Expr

    def eval(self, ctx: Ctx):
        while True:
            self.body.eval(ctx)
            if not is_truthy(self.condition.eval(ctx)):
                break




@dataclass
class BinOp(Expr):
    """Uma operação infixa com dois operandos."""
    left: Expr
    right: Expr
    op: Callable[[Value, Value], Value]

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        right_value = self.right.eval(ctx)
        result = self.op(left_value, right_value)
        
        if isinstance(left_value, float) and left_value.is_integer() and \
           isinstance(right_value, float) and right_value.is_integer() and \
           isinstance(result, float):
            return int(result)
        
        return result

@dataclass
class Var(Expr):
    """Uma variável no código."""
    name: str

    def eval(self, ctx: Ctx):
        try:
            return ctx[self.name]
        except KeyError:
            raise NameError(f"variável {self.name} não existe!")

@dataclass
class Literal(Expr):
    """Representa valores literais no código."""
    value: Value

    def eval(self, ctx: Ctx):
        return self.value



@dataclass
class And(Expr):
    """Operador lógico 'and' com curto-circuito."""
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)

        if not is_truthy(left_value):
            return left_value
        return self.right.eval(ctx)

@dataclass
class Or(Expr):
    """Operador lógico 'or' com curto-circuito."""
    left: Expr
    right: Expr

    def eval(self, ctx: Ctx):
        left_value = self.left.eval(ctx)
        # Usa a nossa nova função is_truthy
        if is_truthy(left_value):
            return left_value
        return self.right.eval(ctx)

@dataclass
class UnaryOp(Expr):
    """Uma operação prefixa com um operando."""
    op: Callable
    value: Expr

    def eval(self, ctx: Ctx):
        v = self.value.eval(ctx)
        return self.op(v)

@dataclass
class Call(Expr):
    """Uma chamada de função."""
    obj: Expr
    params: list[Expr]
    
    def eval(self, ctx: Ctx):
        obj = self.obj.eval(ctx)
        params = [param.eval(ctx) for param in self.params]
        
        if callable(obj):
            return obj(*params)
        raise TypeError(f"{self.obj} não é uma função!")

@dataclass
class This(Expr):
    """Acesso ao `this`."""

@dataclass
class Super(Expr):
    """Acesso a method ou atributo da superclasse."""

@dataclass
class Assign(Expr):
    """Atribuição de variável."""
    name: str
    value: Expr

    def eval(self, ctx: Ctx):
        v = self.value.eval(ctx)
        v = auto_convert(self.name, v)
        ctx[self.name] = v
        return v

@dataclass
class Getattr(Expr):
    """Acesso a atributo de um objeto."""
    value: Expr
    attr: str

    def eval(self, ctx):
        obj = self.value.eval(ctx)
        return getattr(obj, self.attr)
        
@dataclass
class Setattr(Expr):
    """Atribuição de atributo de um objeto."""
    obj: Expr
    attr: str
    value: Expr

    def eval(self, ctx: Ctx):
        obj = self.obj.eval(ctx)
        v = self.value.eval(ctx)
        v = auto_convert(self.attr, v)
        setattr(obj, self.attr, v)
        return v



@dataclass
class Print(Stmt):
    """Representa uma instrução de impressão."""
    expr: Expr
    
    def eval(self, ctx: Ctx):
        value = self.expr.eval(ctx)
        # Usa a nossa nova função lox_str para formatar a saída
        print(lox_str(value))


@dataclass
class Return(Stmt):
    """Representa uma instrução de retorno."""
    value: Expr | None = None
    
    def eval(self, ctx: Ctx):
        # Avalia a expressão do return (se houver)
        return_value = None
        if self.value is not None:
            return_value = self.value.eval(ctx)
        
        # Lança a exceção com o valor do retorno
        raise LoxReturn(return_value)

@dataclass
class VarDef(Stmt):
    """
    Representa uma declaração de variável.
    Ex.: var x = 42;
    """
    name: str
    value: Expr | None = None
    type_annotation: str | None = None

    def eval(self, ctx: Ctx):
        val = None
        if self.value is not None:
            val = self.value.eval(ctx)
        val = auto_convert(self.name, val)
        ctx.var_def(self.name, val)


@dataclass
class If(Stmt):
    """Representa uma instrução condicional."""
    cond: Expr
    then_branch: Stmt
    else_branch: Stmt | None = None

    def eval(self, ctx:Ctx):
        if is_truthy(self.cond.eval(ctx)): 
            return self.then_branch.eval(ctx)
        elif self.else_branch is not None:
            return self.else_branch.eval(ctx)


@dataclass
class While(Stmt):
    """Representa um laço de repetição."""
    expr: Expr
    stmt: Stmt

    def eval(self, ctx: Ctx):

        while is_truthy(self.expr.eval(ctx)):
            self.stmt.eval(ctx)

@dataclass
class Block(Node):
    """Representa bloco de comandos."""
    stmts: list[Stmt]

    def eval(self, ctx: Ctx):

        new_ctx = Ctx(scope={}, parent=ctx)

        for stmt in self.stmts:
            stmt.eval(new_ctx)
        

@dataclass
class Param:
    """Representa um parâmetro de função com tipo opcional."""
    name: str
    type_annotation: str | None = None


@dataclass
class Function(Stmt):
    """Representa uma declaração de função."""
    name: str
    params: list[Param]
    body: Block

    def eval(self, ctx: Ctx):
        param_names = [p.name if isinstance(p, Param) else p for p in self.params]

        lox_function = LoxFunction(self.name, self.params, self.body, ctx)
        

        ctx.var_def(self.name, lox_function)
        
        return None
@dataclass
class Class(Stmt):
    """Representa uma classe."""
